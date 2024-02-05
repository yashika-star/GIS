from django.contrib.gis.geos import GEOSGeometry
import json

from django.db import DatabaseError, connections

from .get_column_names import get_column_names


def create_geojson_in_db(table_name, feature_collection):
    with connections['default'].cursor() as cursor:
        try:
            cursor.execute("BEGIN;")  # Start the transaction
            column_names = get_column_names(feature_collection)
            raw_columns_params = ''
            raw_columns = ''
            columns = ''
            for column_name in column_names:
                raw_columns_params += '%s,'
                raw_columns += f'{column_name},'
                columns += f'{column_name} VARCHAR(255),'

            raw_columns_params += '%s'
            raw_columns += 'geom'
            columns += 'geom geometry(Geometry,4326)'
            cursor.execute(f"CREATE TABLE {table_name} (id BIGSERIAL PRIMARY KEY, {columns});")

            features = feature_collection['features']
            for feature in features:
                column_values = [];
                for column_name in column_names:
                    column_values.append(feature['properties'][column_name] if column_name in feature['properties'] else None)

                geometry = GEOSGeometry(json.dumps(feature['geometry']))
                column_values.append(geometry.ewkb)
                cursor.execute(
                    f"INSERT INTO {table_name} ({raw_columns}) VALUES ({raw_columns_params});", column_values)

            cursor.execute("COMMIT;")  # Complete the transaction
            return {
                "success": True,
                "message": f"Table {table_name} created successfully."
            }
        except DatabaseError as e:
            cursor.execute("ROLLBACK;")  # Rollback the transaction
            return {
                "success": False,
                "message": str(e)
            }