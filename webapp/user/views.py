from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.shortcuts import redirect, render
from django.views import View

class LoginView(View):
    def get(self, request):
        """
        Render the login.html template for GET requests.

        Returns:
            HttpResponse: Rendered template for login page.
        """
        return render(request, "login.html")

    def post(self, request):
        """
        Handle user login for POST requests.

        Args:
            request (HttpRequest): The POST request containing user login data.

        Returns:
            HttpResponse: Redirects to the homepage upon successful login.
                        Rendered template with error message on failed login.
        """
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(
                "query"
            )  # Replace 'home' with the URL name of your home page
        else:
            return render(request, "login.html", {"error": "Invalid credentials"})

class LogoutView(View):
    def get(self, request):
        """
        Handle user logout for GET requests.

        Args:
            request (HttpRequest): The GET request for user logout.

        Returns:
            HttpResponse: Redirects to the homepage after logout.
        """
        logout(request)
        return redirect(
            "login"
        )  # Replace 'login' with the URL name of your login page

class RegisterView(View):
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
            user.groups.add(Group.objects.get(name="reader"))
            user.save()
            # You may perform additional actions like sending a verification email, etc.
            return redirect(
                "login"
            )  # Replace 'login' with the URL name of your login page

        return render(request, "register.html")