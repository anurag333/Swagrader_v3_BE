from django.urls import path
from .in_views import *
from .ta_views import *
from .views import *
from .st_views import *



urlpatterns = [
    path('', CourseListView.as_view()),
    path('enroll', EnrollCourseView.as_view()),
    path('courses/<uuid:course_id>/add-single-user', AddSingleUserView.as_view()),
    path('courses/<uuid:course_id>/update-metadata', UpdateCourseMetadataView.as_view()),
    path('courses/<uuid:course_id>/roster', RosterListView.as_view()),
    path('courses/<uuid:course_id>/roster/<int:pk>', RosterDeleteView.as_view()),
    path('courses/<uuid:course_id>/roster/<int:pk>/update', RosterUpdateView.as_view()),
    path('courses/create', CourseCreateView.as_view()),
    path('courses/<uuid:course_id>/detail-instructor', CourseInstructorDetailUpdateDestroyView.as_view()),
    path('courses/<uuid:course_id>/detail-student', CourseDetailStudentView.as_view()),
    path('courses/<uuid:course_id>/assignments', AssignmentListView.as_view()),
    path('courses/<uuid:course_id>/assignments/create', AssignmentCreateView.as_view()),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>', AssignmentDetailUpdateDestroyView.as_view()),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/outline', assignment_outline_detail),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/publish', assignment_publish),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/questions', QuestionListView.as_view()),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/submit', submit_assignment),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/create-rubrics', create_global_rubrics_instructor),
]
