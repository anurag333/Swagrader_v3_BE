from django.contrib import admin
from django.urls import path, include
from dashboard.views import EmailNamespaceListView
from django.conf import settings
from django.conf.urls.static import static
from dashboard.basic_setup import Setup, purge
from dashboard.front_end_views import *
from django.contrib.auth.views import LoginView, LogoutView
from .views import *


urlpatterns = [
    path('signup/', signup, name="signup"),

]


"""
Strictly for the development mode, Django will serve the files from the server for that purpose, media root will be bounded to `MEDIA_ROOT` defined in the settings. For production mode, Nginx will be used.
"""
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
