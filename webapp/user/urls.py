from django.urls import path

from . import views

urlpatterns = [
    # URL for user login/signin
    path('login', views.LoginView.as_view(), name='login'),
    # URL for user registration/signup
    path('register', views.RegisterView.as_view(), name='register'),
    # URL for user logout/signout
    path('logout', views.LogoutView.as_view(), name='logout'),
]