from django.urls import path
from .in_views import *
from .ta_views import *
from .views import *
from .st_views import *

urlpatterns = [
    path('', CourseListView.as_view()),
    path('enroll', EnrollCourseView.as_view()),
    path('courses/<uuid:course_id>/add-single-user', AddSingleUserView.as_view()),
    path('courses/<uuid:course_id>/update-metadata',
         UpdateCourseMetadataView.as_view()),
    path('courses/<uuid:course_id>/roster', RosterListView.as_view()),
    path('courses/<uuid:course_id>/roster/<int:pk>', RosterDeleteView.as_view()),
    path('courses/<uuid:course_id>/roster/<int:pk>/update',
         RosterUpdateView.as_view()),
    path('courses/create', CourseCreateView.as_view()),
    path('courses/<uuid:course_id>/detail-instructor',
         CourseInstructorDetailUpdateDestroyView.as_view()),
    path('courses/<uuid:course_id>/detail-student',
         CourseDetailStudentView.as_view()),
    path('courses/<uuid:course_id>/assignments', AssignmentListView.as_view()),
    path('courses/<uuid:course_id>/assignments/create',
         AssignmentCreateView.as_view()),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>',
         AssignmentDetailUpdateDestroyView.as_view()),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/outline',
         assignment_outline_detail),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/publish',
         assignment_publish),
    # student
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/questions',
         QuestionListView.as_view()),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/submit',
         submit_assignment),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/close-submissions',
         close_submissions),

    # student
    path('student/courses/<uuid:course_id>',
         CourseDetailStudentView.as_view()),
    # grading
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/grading-method-selection',
         GradingMethodSelection.as_view()),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/stage-grading', stage_grading),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/set-np',
         set_number_of_probes),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/start-grading', start_grading),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/create-rubric',
         global_rubric_create),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/start-peergrading',
         start_peergrading),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/probes-to-check',
         get_probes_to_check),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/grade-probe/<int:probe_id>',
         grade_probe),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/peer-papers-to-check',
         get_peer_papers),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/grade-peer/<int:paper_id>',
         grade_peer),
    #     path('courses/<uuid:course_id>/assignments/<int:assign_id>/grade-peer/<int:paper_id>',
    #          grade_peer),
    path('courses/<uuid:course_id>/assignments/<int:assign_id>/calculate',
         calculate_bonus_and_scores),

]
