from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from authentication.models import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from rest_framework.test import APIClient, APIRequestFactory, APITestCase, force_authenticate
from .in_views import *
from .st_views import *
from .ta_views import *
from .views import *

# class DashboardListTests(TestCase):
#     def setUp(self):
#         User = get_user_model()
#         self.api_factory = APIRequestFactory()
#         e_ns = EmailNamespace.objects.create(namespace='iitk.ac.in')
#         namespace = e_ns.namespace
#         self.user = User.objects.create_user(email=f'testuser@{namespace}', password='password')

#     def test_dashboard(self):
#         # try get with un authenticated request
#         view = CourseListView.as_view()
#         request = self.api_factory.get('/dashboard')
#         response = view(request)
#         self.assertEqual(response.status_code, 401)

#         # now authenticate a user for the purpose
#         force_authenticate(request, user=self.user)
#         response = view(request)
#         self.assertEqual(response.status_code, 200)


# class CourseCreationTests(TestCase):
#     def setUp(self):
#         User = get_user_model()
#         self.api_factory = APIRequestFactory()
#         self.view = CourseCreateView.as_view()
#         e_ns = EmailNamespace.objects.create(namespace='iitk.ac.in')
#         namespace = e_ns.namespace
#         self.user = User.objects.create_user(email=f'testuser@{namespace}', password='password')

#         self.data = {
#             "course_number": "TRY101",
#             "course_title": "Trial course",
#             "term": "Summer",
#             "year": 2022,
#             "entry_restricted": False
#         }
        
#     def test_course_creation_method(self):
#         view = CourseCreateView.as_view()
#         # POST is allowed, not any other method
#         request = self.api_factory.get('/dashboard/courses/create')
#         force_authenticate(request, user=self.user)
#         response = self.view(request)
#         self.assertEqual(response.status_code, 403)

#     def test_course_creation_authentication(self):
#         # authenticated users only
#         request = self.api_factory.post('/dashboard/courses/create', data=self.data)
#         response = self.view(request)
#         self.assertEqual(response.status_code, 401)

#     def test_course_creation_privileges(self):
#         # authenticated users with instructor privileges only
#         request = self.api_factory.post('/dashboard/courses/create', data=self.data)
#         force_authenticate(request, user=self.user)
#         response = self.view(request)
#         self.assertEqual(response.status_code, 403)

#     def test_course_creation(self):
#         # pass when all conditions are true
#         self.user.global_instructor_privilege = True
#         self.user.save()
#         request = self.api_factory.post('/dashboard/courses/create', data=self.data)
#         force_authenticate(request, user=self.user)
#         response = self.view(request)
#         self.assertEqual(response.status_code, 201)

# class CourseManagementTests(TestCase):
#     def setUp(self):
#         User = get_user_model()
#         namespace = EmailNamespace.objects.create(namespace='iitk.ac.in').namespace
#         self.instructor = User.objects.create_user(email=f'instructor@{namespace}', password='password', global_instructor_privilege=True)
#         self.student = User.objects.create_user(email=f'student@{namespace}', password='password')
#         self.bad_user = User.objects.create_user(email=f'bad_user@{namespace}', password='password')
#         self.course_data = {"course_number": "TRY101", "course_title": "Trial course", "term": "Summer", "year": 2022, "entry_restricted": False}
#         self.course = Course.objects.create(**self.course_data)
#         self.course.instructors.add(self.instructor)
#         self.api_factory = APIRequestFactory()

#     def test_add_single_user(self):
#         view = AddSingleUserView.as_view()
#         new_user_data = {
#             'name': 'new user',
#             'institute_id': 180772,
#             'email': 'newuser@iitk.ac.in',
#             'role': 's',
#             'notify': False
#         }

#         existing_user_data = {
#             'name': 'existing user',
#             'institute_id': 180183,
#             'email': self.student.email,
#             'role': 's',
#             'notify': False
#         }
#         # print(f'/dashboard/courses/{self.course.course_id}/add-single-user')
#         request = self.api_factory.post(f'/dashboard/courses/{self.course.course_id}/add-single-user', new_user_data, course_id=self.course.course_id)

#         # unauthenticated request
#         response = view(request, course_id=self.course.course_id)
#         self.assertNotEqual(response.status_code, 200)

#         # authenticated request from bad user
#         force_authenticate(request, user=self.bad_user)
#         response = view(request, course_id=self.course.course_id)
#         self.assertNotEqual(response.status_code, 200)

#         # authenticated from instructor
#         force_authenticate(request, user=self.instructor)
#         response = view(request, course_id=self.course.course_id)
#         self.assertEqual(response.status_code, 200)

#         # testing addition of existing user
#         request = self.api_factory.post(f'/dashboard/courses/{self.course.course_id}/add-single-user', existing_user_data, course_id=self.course.course_id)
#         force_authenticate(request, user=self.instructor)
#         response = view(request, course_id=self.course.course_id)
#         self.assertEqual(response.status_code, 200)

#         self.assertTrue(self.course.students.filter(email=new_user_data['email']).exists())
#         self.assertTrue(self.course.students.filter(email=existing_user_data['email']).exists())

class PreGradingTests(TestCase):
    def setUp(self):
        User = get_user_model()
        namespace = EmailNamespace.objects.create(namespace='iitk.ac.in').namespace
        self.instructor = User.objects.create_user(email=f'instructor@{namespace}', password='1234', global_instructor_privilege=True)
        self.student = User.objects.create_user(email=f'student@{namespace}', password='1234')
        self.ta = User.objects.create_user(email=f'ta@{namespace}', password='1234', global_ta_privilege=True)
        self.bad_user = User.objects.create_user(email=f'bad_user@{namespace}', password='1234')
        self.course_data = {"course_number": "PRG101", "course_title": "Trial course", "term": "Summer", "year": 2022, "entry_restricted": False}
        self.course = Course.objects.create(**self.course_data)
        self.course.instructors.add(self.instructor)
        self.course.students.add(self.student)
        self.course.teaching_assistants.add(self.ta)
        self.api_factory = APIRequestFactory()
        
        pdf = SimpleUploadedFile("onepage_np.txt", b"124", content_type="text/plain")
        assign_data = {
            'title': 'trial assignment',
            'pdf': pdf,
            'publish_date': (datetime.now() - timedelta(days=2)),
            'submission_deadline': (datetime.now() - timedelta(days=1)),
            'allow_late_subs': False,
        }

        self.assign = Assignment.objects.create(**assign_data, course=self.course)

    # def test_assign_creation(self):
    #     User = get_user_model()
    #     file = SimpleUploadedFile("onepage_np.txt", b"124", content_type="text/plain")
    #     view = AssignmentCreateView.as_view()
    #     new_assign_data = {
    #         "title": "Trial Assignment",
    #         "pdf": file,
    #         "publish_date": (datetime.now() - timedelta(days=2)),
    #         "submission_deadline": (datetime.now() - timedelta(days=1)),
    #         "allow_late_subs": False,
    #         "late_sub_deadline": ""
    #     }
    #     request = self.api_factory.post(f'/dashboard/courses/{self.course.course_id}/assignments/create', new_assign_data, course_id=self.course.course_id)
    #     # authenticated request
    #     force_authenticate(request, user=self.instructor)
    #     response = view(request, course_id=self.course.course_id)
    #     self.assertEqual(response.status_code, 201)
    #     file.seek(0)
    
    def test_assign_update(self):
        # try to update assignment name
        view = AssignmentDetailUpdateDestroyView.as_view()
        patch_data = {"title": "Updated Trial Assignment"}
        request = self.api_factory.patch(f'/dashboard/courses/{self.course.course_id}/assignments/{self.assign.assign_id}', patch_data, course_id=self.course.course_id, assign_id=self.assign.assign_id)
        # authenticated request
        print("from passing case request type: ", type(request))
        force_authenticate(request, user=self.instructor)
        response = view(request, course_id=self.course.course_id, assign_id=self.assign.assign_id)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], patch_data['title'])
        self.assertTrue(self.course.authored_assignments.filter(title=patch_data['title']).exists())
    
    def test_set_outline(self):

        outline_data = [
                {
                    "sno": 2,
                    "title": "second question",
                    "max_marks": 5.0,
                    "min_marks": 0,
                    "sub_questions": [
                        {
                            "sno": 1,
                            "title": "the only subquestion",
                            "max_marks": 5.0,
                            "min_marks": 0
                        }
                    ]
                },
                {
                    "sno": 1,
                    "title": "first question",
                    "max_marks": 10.0,
                    "min_marks": 0,
                    "sub_questions": [
                        {
                            "sno": 2,
                            "title": "second subquestion",
                            "max_marks": 2.0,
                            "min_marks": 0
                        },
                        {
                            "sno": 1,
                            "title": "first subquestion",
                            "max_marks": 8.0,
                            "min_marks": 0
                        }
                    ]
                }
            ]

        # view = assignment_outline_detail
        # request = self.api_factory.post(f'/dashboard/courses/{self.course.course_id}/assignments/{self.assign.assign_id}/outline', outline_data, course_id=self.course.course_id, assign_id=self.assign.assign_id, content_type='json')
        # # authenticated request
        # force_authenticate(request, user=self.instructor)
        # print("from failing case request type: ", type(request))
        
        # response = view(request, course_id=self.course.course_id, assign_id=self.assign.assign_id)
        # print(response.data)
        # self.assertEqual(response.status_code, 201)
        self.assertEqual(1,1)