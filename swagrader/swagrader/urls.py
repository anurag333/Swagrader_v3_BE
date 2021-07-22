from django.contrib import admin
from django.urls import path, include
from dashboard.views import EmailNamespaceListView
from django.conf import settings
from django.conf.urls.static import static
from dashboard.basic_setup import Setup, purge
from dashboard.front_end_views import *
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
    path('setup/', Setup.as_view()),
    path('purge/', purge),
    path('admin/', admin.site.urls),
    path('auth/registration/', include('rest_auth.registration.urls')),
    path('auth/', include('rest_auth.urls')),
    path('accounts/', include('allauth.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('namespaces/', EmailNamespaceListView.as_view()),

    path('login', LoginView.as_view(template_name='login_page.html'), name='login'),
    path('logout', LogoutView.as_view(
        template_name='logout_page.html'), name='logout'),
    path('home', home, name='home'),
    path('home/<uuid:course_id>/assignments', assign_list, name='assign_list'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>',
         assign_pdf, name='assign_pdf'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/grade_peer/<int:paper_id>',
         peer_submission, name='peer_submission'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/grade_probe/<int:probe_id>',
         probe_submission, name='probe_submission'),
    path('test',
         test, name='test'),
]


"""
Strictly for the development mode, Django will serve the files from the server for that purpose, media root will be bounded to `MEDIA_ROOT` defined in the settings. For production mode, Nginx will be used.
"""
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
