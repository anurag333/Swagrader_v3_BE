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
from itertools import chain
import time
from .utility import *
import requests


class SetupSerializer(serializers.Serializer):
    pdf = serializers.FileField(required=True)


class Setup(APIView):
    serializer_class = SetupSerializer

    def post(self, request):
        User = get_user_model()
        admin = User.objects.create_superuser('admin@iitk.ac.in', '1234')
        students = []
        ta = []
        instructors = []
        for i in range(10):
            students.append(User.objects.create_user(
                email='student-'+str(i)+'@iitk.ac.in', password=1234, institute_id=180772+i))
        for i in range(3):
            ta.append(User.objects.create_user(
                email='ta-'+str(i)+'@iitk.ac.in', password=1234))

        instructors.append(User.objects.create_user(
            email='instructor@iitk.ac.in', password=1234, global_instructor_privilege=True))

        for user in chain(instructors, students, ta):
            EmailAddress.objects.create(
                email=user.email, user=user, verified=True, primary=True)

        course_data = {
            "course_number": "TRY101",
            "course_title": "Trial course",
            "term": "Summer",
            "year": 2022,
            "entry_restricted": False
        }

        course = Course.objects.create(**course_data, entry_key=''.join(
            [random.choice(string.ascii_letters + string.digits) for n in range(7)]))
        for instructor in instructors:
            course.instructors.add(instructor)
        for student in students:
            course.students.add(student)
        for t in ta:
            course.teaching_assistants.add(t)

        pdf = request.data.get('pdf')
        publish_date = (datetime.now() - timedelta(days=2))
        submission_deadline = (datetime.now() + timedelta(days=1))
        assign_data = {
            'title': 'trial assignment',
            'pdf': pdf,
            'publish_date': publish_date,
            'submission_deadline': submission_deadline,
            'allow_late_subs': False,
        }

        assign = Assignment.objects.create(**assign_data, course=course)
        assign.course = course
        assign.save()
        outline_data = [
            {
                "sno": 2,
                "title": "second question",
                "max_marks": 10.0,
                "min_marks": 0,
                "sub_questions": [
                    {
                        "sno": 1,
                        "title": "the only subquestion",
                        "max_marks": 10.0,
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
                        "max_marks": 5.0,
                        "min_marks": 0
                    },
                    {
                        "sno": 1,
                        "title": "first subquestion",
                        "max_marks": 5.0,
                        "min_marks": 0
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
        GlobalRubric.objects.all().delete()
        GlobalSubrubric.objects.all().delete()
        assign_outline_detail = get_outline_with_rubrics(assign)
        print(assign_outline_detail)
        submissions = []
        for student in students:
            submissions.append(AssignmentSubmission.objects.create(
                author=student, assignment=assign))
            filename = ''.join(
                [random.choice(string.ascii_letters + string.digits) for n in range(7)])
            for q in assign_outline_detail:
                ques_id = q['qid']
                ques = assign.questions.get(ques_id=ques_id)
                qsub = QuestionSubmission.objects.create(
                    submission=submissions[-1], question=ques, pdf=filename+'.pdf')

        assign.current_status = 'method_selected'
        assign.published_for_subs = False
        assign.save()
        print("$$$$$$$$$%%%%%%%%%%%%%%%%%%%")
        print('#pg profile =', AssignmentPeergradingProfile.objects.all().count())
        pg_profile = AssignmentPeergradingProfile.objects.create(assignment=assign, probing_deadline=datetime.now(
        ) - timedelta(days=2), peergrading_deadline=datetime.now() + timedelta(days=1), n_probes=3, peerdist=4)
        print('#pg profile =', AssignmentPeergradingProfile.objects.all().count())
        pg_profile.instructor_graders.set(tuple(instructors))
        pg_profile.ta_graders.set(tuple(ta))
        pg_profile.peergraders.set(tuple(students))
        pg_profile.save()
        print('#pg profile =', AssignmentPeergradingProfile.objects.all().count())
        for ques in assign_outline_detail:
            for sq in ques['sub_questions']:
                sqid = sq['sqid']
                sub_ques = SubQuestion.objects.get(sques_id=sqid)
                for i in range(int(sq['max_marks'])+1):
                    GlobalSubrubric.objects.create(
                        sub_question=sub_ques, marks=i, description=f'give {i} marks')

        URL = f"http://127.0.0.1:8000/dashboard/courses/{course.course_id}/assignments/{assign.assign_id}/start-grading"
        print(URL)
        time.sleep(10)

        assign.current_status = 'rubric_set'
        assign.save()

        return Response({'message': 'Setup Successful!'}, status=200)


@api_view(['GET'])
def purge(request):
    User = get_user_model()
    User.objects.filter(email='admin@iitk.ac.in').delete()
    User.objects.filter(email='instructor@iitk.ac.in').delete()
    for i in range(10):
        User.objects.filter(email='student-'+str(i)+'@iitk.ac.in').delete()
    for i in range(3):
        User.objects.filter(email='ta-'+str(i)+'@iitk.ac.in').delete()

    course = Course.objects.filter(course_title='Trial course').delete()

    return Response({'message': 'purged for setup'}, status=200)


# def post(self, request):
    #     User = get_user_model()

    #     admin = User.objects.create_superuser('admin@iitk.ac.in', '1234')
    #     instructor = User.objects.create_user(email='instructor@iitk.ac.in', password=1234, global_instructor_privilege=True)
    #     student = User.objects.create_user(email='student@iitk.ac.in', password=1234, institute_id=180772)
    #     ta = User.objects.create_user(email='ta@iitk.ac.in', password=1234)

    #     for user in [instructor, student, ta]:
    #         EmailAddress.objects.create(email=user.email, user=user, verified=True, primary=True)

    #     course_data = {
    #         "course_number": "TRY101",
    #         "course_title": "Trial course",
    #         "term": "Summer",
    #         "year": 2022,
    #         "entry_restricted": False
    #     }

    #     course = Course.objects.create(**course_data, entry_key = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(7)]))
    #     course.instructors.add(instructor)
    #     course.students.add(student)
    #     course.teaching_assistants.add(ta)

    #     pdf = request.data.get('pdf')
    #     publish_date = (datetime.now() - timedelta(days=2))
    #     submission_deadline = (datetime.now() - timedelta(days=1))
    #     assign_data = {
    #         'title': 'trial assignment',
    #         'pdf': pdf,
    #         'publish_date': publish_date,
    #         'submission_deadline': submission_deadline,
    #         'allow_late_subs': False,
    #     }

    #     assign = Assignment.objects.create(**assign_data, course=course)

    #     outline_data = [
    #         {
    #             "sno": 2,
    #             "title": "second question",
    #             "max_marks": 5.0,
    #             "min_marks": 0,
    #             "sub_questions": [
    #                 {
    #                     "sno": 1,
    #                     "title": "the only subquestion",
    #                     "max_marks": 5.0,
    #                     "min_marks": 0
    #                 }
    #             ]
    #         },
    #         {
    #             "sno": 1,
    #             "title": "first question",
    #             "max_marks": 10.0,
    #             "min_marks": 0,
    #             "sub_questions": [
    #                 {
    #                     "sno": 2,
    #                     "title": "second subquestion",
    #                     "max_marks": 2.0,
    #                     "min_marks": 0
    #                 },
    #                 {
    #                     "sno": 1,
    #                     "title": "first subquestion",
    #                     "max_marks": 8.0,
    #                     "min_marks": 0
    #                 }
    #             ]
    #         }
    #     ]

    #     for ques in outline_data:
    #         sub_questions = ques.pop('sub_questions')
    #         question = Question.objects.create(**ques, parent_assign=assign)
    #         for sq in sub_questions:
    #             SubQuestion.objects.create(**sq, parent_ques=question)

    #     assign.current_status = 'published'
    #     assign.published_for_subs = True
    #     assign.save()
    #     return Response({'message': 'Setup Successful!'}, status=200)


# rubric_create = {
#     "questions": [
#         {
#             "qid": 1,
#             "max_marks": 5,
#             "min_marks": 0,
#             "rubrics": [

#             ],
#             "sub_questions": [
#                 {
#                     "sqid": 1,
#                     "max_marks": 5,
#                     "min_marks": 0,
#                     "sub_rubrics": [
#                         {
#                             "marks": 5,
#                             "description": "Step 1 is correct"
#                         },
#                         {
#                             "marks": 3,
#                             "description": "Step 1 is correct"
#                         }
#                     ]
#                 }
#             ]
#         },
#         {
#             "qid": 2,
#             "max_marks": 10,
#             "min_marks": 0,
#             "rubrics": [

#             ],
#             "sub_questions": [
#                 {
#                     "sqid": 2,
#                     "max_marks": 5,
#                     "min_marks": 0,
#                     "sub_rubrics": [
#                         {
#                             "marks": 5,
#                             "description": "Step 1 is correct"
#                         },
#                         {
#                             "marks": 3,
#                             "description": "Step 1 is correct"
#                         }
#                     ]
#                 },
#                 {
#                     "sqid": 3,
#                     "max_marks": 8,
#                     "min_marks": 0,
#                     "sub_rubrics": [
#                         {
#                             "marks": 5,
#                             "description": "Step 1 is correct"
#                         },
#                         {
#                             "marks": 3,
#                             "description": "Step 1 is correct"
#                         }
#                     ]
#                 }
#             ]
#         }
#     ]
# }


# grade probe
# grade_PROBE = {
#     "questions": [
#         {
#             "qid": 2,
#             "max_marks": 10.0,
#             "min_marks": 0.0,
#             "rubrics": [],
#             "sub_questions": [
#                 {
#                     "sqid": 3,
#                     "max_marks": 8.0,
#                     "min_marks": 0.0,
#                     "sub_rubrics": [
#                         {
#                             "sub_rubric_id": 53,
#                             "marks": 5,
#                             "description": "Step 1 is correct"
#                         }
#                     ],
#                     "comment": {
#                         "marks": 1,
#                         "description": "temp comment"
#                     }
#                 },
#                 {
#                     "sqid": 2,
#                     "max_marks": 2.0,
#                     "min_marks": 0.0,
#                     "sub_rubrics": [
#                         {
#                             "sub_rubric_id": 51,
#                             "marks": 5,
#                             "description": "Step 1 is correct"
#                         }
#                     ],
#                     "comment": {
#                         "marks": 1,
#                         "description": "temp comment"
#                     }
#                 }
#             ],
#             "comment": {
#                 "marks": 1,
#                 "description": "temp comment"
#             }
#         },
#         {
#             "qid": 1,
#             "max_marks": 5.0,
#             "min_marks": 0.0,
#             "rubrics": [],
#             "sub_questions": [
#                 {
#                     "sqid": 1,
#                     "max_marks": 5.0,
#                     "min_marks": 0.0,
#                     "sub_rubrics": [
#                         {
#                             "sub_rubric_id": 49,
#                             "marks": 5,
#                             "description": "Step 1 is correct"
#                         }
#                     ],
#                     "comment": {
#                         "marks": 1,
#                         "description": "temp comment"
#                     }
#                 }
#             ],
#             "comment": {
#                 "marks": 1,
#                 "description": "temp comment"
#             }
#         }
#     ]
# }
# select one of the rubrics
# grade_probe = {"questions":[
#     {
#         "qid": 84,
#         "max_marks": 10.0,
#         "min_marks": 0.0,
#         "rubrics": [],
#         "sub_questions": [
#             {
#                 "sqid": 126,
#                 "max_marks": 5.0,
#                 "min_marks": 0.0,
#                 "sub_rubrics": [
#                     {
#                         "sub_rubric_id": 703,
#                         "marks": 0,
#                         "description": "give 0 marks"
#                     },
#                     {
#                         "sub_rubric_id": 704,
#                         "marks": 1,
#                         "description": "give 1 marks"
#                     },
#                     {
#                         "sub_rubric_id": 705,
#                         "marks": 2,
#                         "description": "give 2 marks"
#                     },
#                     {
#                         "sub_rubric_id": 706,
#                         "marks": 3,
#                         "description": "give 3 marks"
#                     },
#                     {
#                         "sub_rubric_id": 707,
#                         "marks": 4,
#                         "description": "give 4 marks"
#                     }
#                 ]
#             },
#             {
#                 "sqid": 125,
#                 "max_marks": 5.0,
#                 "min_marks": 0.0,
#                 "sub_rubrics": [
#                     {
#                         "sub_rubric_id": 708,
#                         "marks": 0,
#                         "description": "give 0 marks"
#                     },
#                     {
#                         "sub_rubric_id": 709,
#                         "marks": 1,
#                         "description": "give 1 marks"
#                     },
#                     {
#                         "sub_rubric_id": 710,
#                         "marks": 2,
#                         "description": "give 2 marks"
#                     },
#                     {
#                         "sub_rubric_id": 711,
#                         "marks": 3,
#                         "description": "give 3 marks"
#                     },
#                     {
#                         "sub_rubric_id": 712,
#                         "marks": 4,
#                         "description": "give 4 marks"
#                     }
#                 ]
#             }
#         ],
#         "comment": {
#             "marks": 0,
#             "description": "temp cmnt",
#         }
#     },
#     {
#         "qid": 83,
#         "max_marks": 10.0,
#         "min_marks": 0.0,
#         "rubrics": [],
#         "sub_questions": [
#             {
#                 "sqid": 124,
#                 "max_marks": 10.0,
#                 "min_marks": 0.0,
#                 "sub_rubrics": [
#                     {
#                         "sub_rubric_id": 713,
#                         "marks": 0,
#                         "description": "give 0 marks"
#                     },
#                     {
#                         "sub_rubric_id": 714,
#                         "marks": 1,
#                         "description": "give 1 marks"
#                     },
#                     {
#                         "sub_rubric_id": 715,
#                         "marks": 2,
#                         "description": "give 2 marks"
#                     },
#                     {
#                         "sub_rubric_id": 716,
#                         "marks": 3,
#                         "description": "give 3 marks"
#                     },
#                     {
#                         "sub_rubric_id": 717,
#                         "marks": 4,
#                         "description": "give 4 marks"
#                     },
#                     {
#                         "sub_rubric_id": 718,
#                         "marks": 5,
#                         "description": "give 5 marks"
#                     },
#                     {
#                         "sub_rubric_id": 719,
#                         "marks": 6,
#                         "description": "give 6 marks"
#                     },
#                     {
#                         "sub_rubric_id": 720,
#                         "marks": 7,
#                         "description": "give 7 marks"
#                     },
#                     {
#                         "sub_rubric_id": 721,
#                         "marks": 8,
#                         "description": "give 8 marks"
#                     },
#                     {
#                         "sub_rubric_id": 722,
#                         "marks": 9,
#                         "description": "give 9 marks"
#                     }
#                 ]
#             }
#         ],
#         "comment": {
#             "marks": 0,
#             "description": "temp cmnt",
#         }
#     }
# ]
# }
# grade_porbe = {"questions": [
#     {
#         "qid": 84,
#         "max_marks": 10.0,
#         "min_marks": 0.0,
#         "rubrics": [],
#         "sub_questions": [
#             {
#                 "sqid": 126,
#                 "max_marks": 5.0,
#                 "min_marks": 0.0,
#                 "sub_rubrics": [
#                     {
#                         "sub_rubric_id": 707,
#                         "marks": 4,
#                         "description": "give 4 marks"
#                     }
#                 ]
#             },
#             {
#                 "sqid": 125,
#                 "max_marks": 5.0,
#                 "min_marks": 0.0,
#                 "sub_rubrics": [
#                     {
#                         "sub_rubric_id": 712,
#                         "marks": 4,
#                         "description": "give 4 marks"
#                     }
#                 ]
#             }
#         ],
#         "comment": {
#             "marks": 0,
#             "description": "temp cmnt"
#         }
#     },
#     {
#         "qid": 83,
#         "max_marks": 10.0,
#         "min_marks": 0.0,
#         "rubrics": [],
#         "sub_questions": [
#             {
#                 "sqid": 124,
#                 "max_marks": 10.0,
#                 "min_marks": 0.0,
#                 "sub_rubrics": [
#                     {
#                         "sub_rubric_id": 722,
#                         "marks": 9,
#                         "description": "give 9 marks"
#                     }
#                 ]
#             }
#         ],
#         "comment": {
#             "marks": 0,
#             "description": "temp cmnt"
#         }
#     }
# ]
# }


# grade_peer = {"questions": [
#     {
#         "qid": 94,
#         "max_marks": 10.0,
#         "min_marks": 0.0,
#         "rubrics": [],
#         "sub_questions": [
#             {
#                 "sqid": 141,
#                 "max_marks": 5.0,
#                 "min_marks": 0.0,
#                 "sub_rubrics": [
#                     {
#                         "sub_rubric_id": 707,
#                         "marks": 4,
#                         "description": "give 4 marks"
#                     }
#                 ]
#             },
#             {
#                 "sqid": 140,
#                 "max_marks": 5.0,
#                 "min_marks": 0.0,
#                 "sub_rubrics": [
#                     {
#                         "sub_rubric_id": 712,
#                         "marks": 4,
#                         "description": "give 4 marks"
#                     }
#                 ]
#             }
#         ]
#     },
#     {
#         "qid": 93,
#         "max_marks": 10.0,
#         "min_marks": 0.0,
#         "rubrics": [],
#         "sub_questions": [
#             {
#                 "sqid": 139,
#                 "max_marks": 10.0,
#                 "min_marks": 0.0,
#                 "sub_rubrics": [
#                     {
#                         "sub_rubric_id": 722,
#                         "marks": 9,
#                         "description": "give 9 marks"
#                     }
#                 ]
#             }
#         ]
#     }
# ]
# }
