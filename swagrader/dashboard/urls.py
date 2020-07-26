from django.urls import path
from .views import *

urlpatterns = [
    path('', CourseListView.as_view()),
    path('course/<uuid:course_id>/add-single-user', AddSingleUserView.as_view()),
    path('course/<uuid:course_id>/update-metadata', UpdateCourseMetadataView.as_view()),
    path('course/<uuid:course_id>/roster', RosterListView.as_view()),
    path('course/<uuid:course_id>/roster/<int:pk>/delete', RosterDeleteView.as_view()),
    path('course/<uuid:course_id>/roster/<int:pk>/update', RosterUpdateView.as_view()),
    path('course/create', CourseCreateView.as_view()),
]