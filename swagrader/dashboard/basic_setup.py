from .models import *
from authentication.models import *
from .in_views import *
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.files import File
from rest_framework.views import APIView
from rest_framework import serializers
from allauth.account.models import EmailAddress

class SetupSerializer(serializers.Serializer):
    pdf = serializers.FileField(required=True)

class Setup(APIView):
    serializer_class = SetupSerializer
    def post(self, request):
        User = get_user_model()
        admin = User.objects.create_superuser('admin@iitk.ac.in', '1234')
        instructor = User.objects.create_user(email='instructor@iitk.ac.in', password=1234, global_instructor_privilege=True)
        student = User.objects.create_user(email='student@iitk.ac.in', password=1234, institute_id=180772)
        ta = User.objects.create_user(email='ta@iitk.ac.in', password=1234)

        for user in [instructor, student, ta]:
            EmailAddress.objects.create(email=user.email, user=user, verified=True, primary=True)

        course_data = {
            "course_number": "TRY101",
            "course_title": "Trial course",
            "term": "Summer",
            "year": 2022,
            "entry_restricted": False
        }

        course = Course.objects.create(**course_data, entry_key = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(7)]))
        course.instructors.add(instructor)
        course.students.add(student)
        course.teaching_assistants.add(ta)

        pdf = request.data.get('pdf')
        publish_date = (datetime.now() - timedelta(days=2))
        submission_deadline = (datetime.now() - timedelta(days=1))
        assign_data = {
            'title': 'trial assignment',
            'pdf': pdf,
            'publish_date': publish_date,
            'submission_deadline': submission_deadline,
            'allow_late_subs': False,
        }

        assign = Assignment.objects.create(**assign_data, course=course)

        outline_data = [
            {
                "sno": 2,
                "title": "second question",
                "marks": 5.0,
                "sub_questions": [
                    {
                        "sno": 1,
                        "title": "the only subquestion",
                        "marks": 5.0
                    }
                ]
            },
            {
                "sno": 1,
                "title": "first question",
                "marks": 10.0,
                "sub_questions": [
                    {
                        "sno": 2,
                        "title": "second subquestion",
                        "marks": 2.0
                    },
                    {
                        "sno": 1,
                        "title": "first subquestion",
                        "marks": 8.0
                    }
                ]
            }
        ]

        for ques in outline_data:
            sub_questions = ques.pop('sub_questions')
            question = Question.objects.create(**ques, parent_assign=assign)
            for sq in sub_questions:
                SubQuestion.objects.create(**sq, parent_ques=question)

        assign.current_status = 'published'
        assign.published_for_subs = True
        assign.save()
        return Response({'message': 'Setup Successful!'}, status=200)

@api_view(['POST'])
def purge(request):
    User = get_user_model()
    User.objects.filter(email='admin@iitk.ac.in').delete()
    User.objects.filter(email='instructor@iitk.ac.in').delete()
    User.objects.filter(email='student@iitk.ac.in').delete()
    User.objects.filter(email='ta@iitk.ac.in').delete()

    return Response({'message': 'purged for setup'}, status=200)

