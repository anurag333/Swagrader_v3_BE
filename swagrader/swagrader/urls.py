from django.contrib import admin
from django.urls import path, include
from dashboard.views import EmailNamespaceListView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/registration/', include('rest_auth.registration.urls')),
    path('auth/', include('rest_auth.urls')),
    path('accounts/', include('allauth.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('namespaces/', EmailNamespaceListView.as_view())
]


"""
Strictly for the development mode, Django will serve the files from the server for that purpose, media root will be bounded to `MEDIA_ROOT` defined in the settings. For production mode, Nginx will be used.
"""
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)