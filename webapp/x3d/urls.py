from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.views.static import serve
import os

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("assetdetails", views.assetDetails , name="assetDetails"),
]

# Only for development! Don't use this in production.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# For production, use the following configuration to serve protected media files:
# urlpatterns += [
#     path('media/<path:path>/', login_required(serve), {'document_root': settings.MEDIA_ROOT}),
# ]