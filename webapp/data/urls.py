from django.urls import path

from . import views

urlpatterns = [
    path("", views.query, name="query"),
    path("upload", views.upload, name="upload"),
    path("age", views.age_viewer, name="age_viewer"),
    path("kg/<str:table_name>", views.kg, name="kg"),
    path("save-json", views.save_json, name="save-json"),
    path("3dviewer", views.threedviewer, name="3dviewer"),
    path("map", views.mapviewer, name="map"),
    path("scene", views.sceneviewer, name="scene")
]