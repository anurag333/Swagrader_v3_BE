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
    path('dashboard/', include('authentication.urls')),
    path('namespaces/', EmailNamespaceListView.as_view()),
    path('', LoginView.as_view(template_name='login_page.html'), name='login'),
    path('login', LoginView.as_view(template_name='login_page.html'), name='login'),
    path('logout', LogoutView.as_view(
        template_name='logout_page.html'), name='logout'),
    path('home', home, name='home'),
    path('home/<uuid:course_id>/assignments', assign_list, name='assign_list'),
    path('home/<uuid:course_id>/assignments/create-roster',
         create_roster, name='create_roster'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>',
         assign_pdf, name='assign_pdf'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/outline',
         fe_set_outline, name='fe_set_outline'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/set-rubric',
         set_rubric, name='set_rubric'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/submit-assignment',
         fe_submit_assignment, name='fe_submit_assignment'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/update-assign-details',
         update_assign_details, name='update_assign_details'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/assign-roster',
         create_assign_roster, name='create_assign_roster'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/method-select',
         fe_method_select, name='fe_method_select'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/grade-peer/<int:paper_id>',
         peer_submission, name='peer_submission'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/grade-probe/<int:probe_id>',
         probe_submission, name='probe_submission'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/probe-list',
         probe_list, name='probe_list'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/peer-list',
         peer_list, name='peer_list'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/calc-score',
         calc_score, name='calc_score'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/see-grades',
         see_grades, name='see_grades'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/student-marks',
         student_marks, name='student_marks'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/select-ta',
         select_ta, name='select_ta'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/set-regrading-deadline',
         set_regrading_deadline, name='set_regrading_deadline'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/regrading-request',
         fe_regrading_request, name='fe_regrading_request'),
    path('home/<uuid:course_id>/assignments/<int:assign_id>/regrading-request-papers',
         fe_regrading_request_papers, name='fe_regrading_request_papers'),
    path('test',
         test, name='test'),
]


"""
Strictly for the development mode, Django will serve the files from the server for that purpose, media root will be bounded to `MEDIA_ROOT` defined in the settings. For production mode, Nginx will be used.
"""
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
