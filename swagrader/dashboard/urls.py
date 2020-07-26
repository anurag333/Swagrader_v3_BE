from django.urls import path
from .views import *

urlpatterns = [
    path('', CourseListView.as_view()),
    path('course/<uuid:course_uid>/add-single-user', AddSingleUserView.as_view()),
    path('course/create', CourseCreateView.as_view()),

]