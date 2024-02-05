import json
import re
from django.db import connections
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.template import loader
from django.views import View
from psycopg2 import DatabaseError
from django.views.decorators.csrf import csrf_exempt

from .helpers.create_kg_in_db import create_kg_in_db

from .helpers.geo_converter import GeoConverter

from .helpers.create_geojson_in_db import create_geojson_in_db

@csrf_exempt
def save_json(request):
    context = {}
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode('utf-8'))
            content = body.get("data", None)
            print(content)
            table_name = body.get("file_name", None)
            result = create_kg_in_db(table_name, content)
            context["message"] = result["message"]
            context["success"] = result["success"]

            return JsonResponse(context)
        except json.JSONDecodeError:
            return JsonResponse({'error':'Invalid JSON data'}, status=400)

    return JsonResponse({'error':'Invalid request method'}, status=405)

@login_required(redirect_field_name="returnUrl")
def upload(request):
    # table_name = "person"
    # feature_collection = {
    # "type": "FeatureCollection",
    # "features": [
    #         {
    #             "type": "Feature",
    #             "properties": {
    #                 "name": "Jonathan",
    #                 "age": 45
    #             },
    #             "geometry": {
    #                 "type": "Point",
    #                 "coordinates": [0, 0]
    #             }
    #         },
    #         {
    #             "type": "Feature",
    #             "properties": {
    #                 "name": "Chris",
    #                 "age": 89
    #             },
    #             "geometry": {
    #                 "type": "Point",
    #                 "coordinates": [20, 0]
    #             }
    #         },
    #     ]
    # }
    context = {}
    if request.method == "POST":
        table_name = request.POST.get("tablename", None)
        fileType = request.POST.get("file-type", None)
        if table_name is not None and fileType is not None:
            file = request.FILES.get("file")

            content = None
            if fileType == "geojson":
                content = file.read().decode('utf-8')
            elif fileType == "shp":
                content = GeoConverter.shapefile_zip_to_geojson(file.read())
            elif fileType == "kml":
                content = GeoConverter.kml_to_geojson(
                    file.read().decode('utf-8'))

            if content is not None:
                result = create_geojson_in_db(table_name, json.loads(content))
                context["message"] = result["message"]
                context["success"] = result["success"]
            else:
                if fileType == "kg":
                    content = file.read().decode('utf-8')
                    result = create_kg_in_db(table_name, json.loads(content))
                    context["message"] = result["message"]
                    context["success"] = result["success"]
                else:
                    context["success"] = False
                    context["message"] = "Invalid file type."

        else:
            context["success"] = False
            context["message"] = "Invalid table name."

    template = loader.get_template("index.html")
    return HttpResponse(template.render(context, request))

@login_required(redirect_field_name="returnUrl")
@user_passes_test(test_func=lambda user: user.is_superuser or user.groups.filter(name__in=['reader', 'admin']).exists(), login_url='/upload')
def query(request):
    context = {}
    # context["columns"] = ["name", "age"]
    # context["rows"] = [
    #     ["Abdullah", 25],
    #     ["Atharv", 65]
    # ]
    # print("ROLES ==> " + ",".join([g.name for g in request.user.groups.all()]))
    if request.method == "GET" or request.method == "POST":
        user_roles = [g.name for g in request.user.groups.all()]
        is_super_admin = request.user.is_superuser
        is_admin = 'admin' in user_roles

        with connections['default'].cursor() as cursor:
            try:
                cursor.execute("""
                    with spatial_tables as (
                        select f_table_schema || '.' || f_table_name as table_name, f_geometry_column as geom_column_name from geometry_columns
                    )
                    SELECT table_schema || '.' || table_name, null as geom_column_name FROM information_schema.tables WHERE table_schema not in ('information_schema', 'pg_catalog', 'topology') and table_schema not in (SELECT name::text FROM ag_catalog."ag_graph") and table_type = 'BASE TABLE' and table_name != 'spatial_ref_sys' and table_name not in (select table_name from spatial_tables)
                    union all
                    select * from spatial_tables;
                    """)
                result = cursor.fetchall()
                if not is_super_admin and not is_admin:
                    result = [r for r in result if r[0].startswith('public.')]
                context["tables"] = result
            except DatabaseError as e:
                context["table_list_error"] = str(e)

            if request.method == "POST":
                query = request.POST.get("sql", None)
                # query = query.lower()
                if query is not None and len(query) > 0:
                    context["query"] = query
                    # Convert the query into a list of capitalized words
                    query_clauses = [str(i).capitalize() for i in str(query).split()]

                    # Define different levels of database query commands
                    admin_queries = ["Create", "Insert", "Update", "Alter"]
                    super_admin_queries = ["Delete", "Drop", "Remove", "Truncate", "Grant", "Revoke", "@"]

                    should_execute_query = True
                    if not is_super_admin:
                        if is_admin:
                            for query_clause in query_clauses:
                                if query_clause in super_admin_queries:
                                    context["table_error"] = "You are not authorized to run commands like: " + ",".join(super_admin_queries)
                                    should_execute_query = False
                                    break
                        else:
                            # For reader role
                            for i, query_clause in enumerate(query_clauses):
                                if query_clause in admin_queries:
                                    context["table_error"] = "You are not authorized to run commands like: " + ",".join(admin_queries) + "," + ",".join(super_admin_queries)
                                    should_execute_query = False
                                    break

                                # For reader change the schema to public
                                if query_clause == "From" and not query_clauses[i + 1].startswith('('):
                                    lc = query_clauses[i + 1]
                                    c = lc.split(".")
                                    if len(c) == 2 and c[0].casefold() != 'public.':
                                        context["table_error"] = "You are not authorized to query schemas other than public."
                                        should_execute_query = False
                                        break
                                    elif len(c) == 1 and not '.' in lc:
                                        pattern = re.compile(lc, re.IGNORECASE)
                                        query = pattern.sub('public.' + c[0], query, 1)
                                        # query = query.replace(lc, 'public.' + c[0])


                    if should_execute_query:
                        try:
                            cursor.execute(query)
                            if query_clauses[0] == 'Select':
                                result = cursor.fetchall()
                                context["columns"] = [desc[0]
                                                    for desc in cursor.description]
                                if len(result) > 0:
                                    context["rows"] = result
                            else:
                                context["message"] = "Query executed successfully."
                        except DatabaseError as e:
                            context["table_error"] = str(e)

    template = loader.get_template("query.html")
    return HttpResponse(template.render(context, request))

@login_required(redirect_field_name="returnUrl")
def age_viewer(request):
    context = {}
    if request.method == "GET":
        template = loader.get_template("age_viewer.html")
        return HttpResponse(template.render(context, request))

@login_required(redirect_field_name="returnUrl")
def threedviewer(request):
    context = {}
    if request.method == "GET":
        template = loader.get_template("3dviewer.html")
        return HttpResponse(template.render(context, request))


@login_required(redirect_field_name="returnUrl")
def kg(request, table_name):
    if request.method == "GET":
        with connections['default'].cursor() as cursor:
            try:
                cursor.execute(f"""
                    SELECT JSON_BUILD_OBJECT('nodes', (SELECT ARRAY_AGG(J) FROM
		(SELECT JSON_BUILD_OBJECT('id', KEY, 'name', NAME) AS J FROM {table_name}_kg_nodes) T), 'links', (SELECT ARRAY_AGG(J) FROM
		(SELECT JSON_BUILD_OBJECT('source', source, 'target', target, 'desc', description) AS J FROM {table_name}_kg_links) T));
                    """)
                result = cursor.fetchone()
                return JsonResponse({
                    'success': True,
                    'data': result
                })
            except DatabaseError as e:
                print(str(e))
                return JsonResponse({
                    'success': False
                })

    def get(self, request):
        """
        Render the signup.html template for GET requests.

        Returns:
            HttpResponse: Rendered template for signup page.
        """
        return render(request, "register.html")

    def post(self, request):
        """
        Handle the user signup for POST requests.

        Args:
            request (HttpRequest): The POST request containing user signup data.

        Returns:
            HttpResponse: Redirects to the login page upon successful signup.
                        Rendered template with error message on failed signup.
        """
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm-password")
        if password == confirm_password:
            # Create a new user
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            # You may perform additional actions like sending a verification email, etc.
            return redirect(
                "login"
            )  # Replace 'login' with the URL name of your login page

        return render(request, "register.html")
@login_required(redirect_field_name="returnUrl")
def mapviewer(request):
    context = {}
    if request.method == "GET":
        template = loader.get_template("map.html")
        return HttpResponse(template.render(context, request))

@login_required(redirect_field_name="returnUrl")
def sceneviewer(request):
    context = {}
    if request.method == "GET":
        template = loader.get_template("scene.html")
        return HttpResponse(template.render(context, request))