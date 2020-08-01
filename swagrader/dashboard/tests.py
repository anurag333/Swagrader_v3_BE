from django.test import TestCase, RequestFactory
from authentication.models import *
from django.contrib.auth import get_user_model
from .models import *
from rest_framework.test import APIClient, APIRequestFactory, APITestCase, force_authenticate
from .in_views import *
from .st_views import *
from .ta_views import *
from .views import *

class DashboardListTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.api_factory = APIRequestFactory()
        e_ns = EmailNamespace.objects.create(namespace='iitk.ac.in')
        namespace = e_ns.namespace
        self.user = User.objects.create_user(email=f'testuser@{namespace}', password='password')

    def test_dashboard(self):
        # try get with un authenticated request
        view = CourseListView.as_view()
        request = self.api_factory.get('/dashboard')
        response = view(request)
        self.assertEqual(response.status_code, 401)

        # now authenticate a user for the purpose
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)


class CourseCreationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.api_factory = APIRequestFactory()
        self.view = CourseCreateView.as_view()
        e_ns = EmailNamespace.objects.create(namespace='iitk.ac.in')
        namespace = e_ns.namespace
        self.user = User.objects.create_user(email=f'testuser@{namespace}', password='password')

        self.data = {
            "course_number": "TRY101",
            "course_title": "Trial course",
            "term": "Summer",
            "year": 2022,
            "entry_restricted": False
        }
        
    def test_course_creation_method(self):
        view = CourseCreateView.as_view()
        # POST is allowed, not any other method
        request = self.api_factory.get('/dashboard/courses/create')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 403)

    def test_course_creation_authentication(self):
        # authenticated users only
        request = self.api_factory.post('/dashboard/courses/create', data=self.data)
        response = self.view(request)
        self.assertEqual(response.status_code, 401)

    def test_course_creation_privileges(self):
        # authenticated users with instructor privileges only
        request = self.api_factory.post('/dashboard/courses/create', data=self.data)
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 403)

    def test_course_creation(self):
        # pass when all conditions are true
        self.user.global_instructor_privilege = True
        self.user.save()
        request = self.api_factory.post('/dashboard/courses/create', data=self.data)
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 201)

class CourseManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        namespace = EmailNamespace.objects.create(namespace='iitk.ac.in').namespace
        self.instructor = User.objects.create_user(email=f'instructor@{namespace}', password='password', global_instructor_privilege=True)
        self.student = User.objects.create_user(email=f'student@{namespace}', password='password')
        self.bad_user = User.objects.create_user(email=f'bad_user@{namespace}', password='password')
        self.course_data = {"course_number": "TRY101", "course_title": "Trial course", "term": "Summer", "year": 2022, "entry_restricted": False}
        self.course = Course.objects.create(**self.course_data)
        self.course.instructors.add(self.instructor)
        self.api_factory = APIRequestFactory()

    def test_add_single_user(self):
        view = AddSingleUserView.as_view()
        new_user_data = {
            'name': 'new user',
            'institute_id': 180772,
            'email': 'newuser@iitk.ac.in',
            'role': 's',
            'notify': False
        }

        existing_user_data = {
            'name': 'existing user',
            'institute_id': 180183,
            'email': self.student.email,
            'role': 's',
            'notify': False
        }
        # print(f'/dashboard/courses/{self.course.course_id}/add-single-user')
        request = self.api_factory.post(f'/dashboard/courses/{self.course.course_id}/add-single-user', new_user_data, course_id=self.course.course_id)

        # unauthenticated request
        response = view(request, course_id=self.course.course_id)
        self.assertNotEqual(response.status_code, 200)

        # authenticated request from bad user
        force_authenticate(request, user=self.bad_user)
        response = view(request, course_id=self.course.course_id)
        self.assertNotEqual(response.status_code, 200)

        # authenticated from instructor
        force_authenticate(request, user=self.instructor)
        response = view(request, course_id=self.course.course_id)
        self.assertEqual(response.status_code, 200)

        # testing addition of existing user
        request = self.api_factory.post(f'/dashboard/courses/{self.course.course_id}/add-single-user', existing_user_data, course_id=self.course.course_id)
        force_authenticate(request, user=self.instructor)
        response = view(request, course_id=self.course.course_id)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(self.course.students.filter(email=new_user_data['email']).exists())
        self.assertTrue(self.course.students.filter(email=existing_user_data['email']).exists())


    
    