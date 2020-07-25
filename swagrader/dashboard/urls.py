from django.urls import path
from .views import CourseListView, CourseCreateView

urlpatterns = [
    path('', CourseListView.as_view()),
    path('course/create', CourseCreateView.as_view()),

]