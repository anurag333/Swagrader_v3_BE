import re
from django.db.models.query_utils import Q
from django.shortcuts import render
from rest_framework import generics, views, permissions, mixins
from rest_framework.response import Response
from rest_framework.decorators import api_view
from authentication.models import EmailNamespace
from authentication.serializers import EmailNamespaceSerializer
from .serializers import *
from .permissions import *
from .models import *
from itertools import chain
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import status
import random
import string
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .utility import *
from rest_framework.renderers import JSONRenderer
from .trupeqa import *
from django.views.decorators.csrf import csrf_exempt


@login_required
@api_view(['GET'])
def close_submissions(request, course_id, assign_id):
    if request.method == 'GET':
        try:
            curr_course = Course.objects.get(course_id=course_id)
            curr_assign = curr_course.authored_assignments.get(
                assign_id=assign_id)
        except Course.DoesNotExist or Assignment.DoesNotExist:
            raise Http404

        if request.user not in curr_course.instructors.all():
            return Response({'message': 'You are not allowed for this operation.'}, status=status.HTTP_403_FORBIDDEN)

        if curr_assign.current_status == 'published':
            curr_assign.current_status = 'subs_closed'
            curr_assign.published_for_subs = False
            curr_assign.save()
            return Response({'message': 'Assignment closed successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'This operation is only allowed for published assignments.'}, status=status.HTTP_403_FORBIDDEN)

        # if curr_assign.publish_date <= timezone.now() < curr_assign.submission_deadline:
        #     curr_assign.current_status = 'published'
        #     curr_assign.published_for_subs = False
        #     curr_assign.save()
        #     print(curr_assign.status)
        #     return Response({'message': 'Assignment published successfully.'}, status=status.HTTP_200_OK)
        # return Response({'message': 'Current date is not in range [publish_date, submission_deadline), wait or update the deadline/publish_date.'}, status=status.HTTP_403_FORBIDDEN)


@login_required
@api_view(['GET'])
def assignment_publish(request, course_id, assign_id):
    if request.method == 'GET':
        try:
            curr_course = Course.objects.get(course_id=course_id)
            curr_assign = curr_course.authored_assignments.get(
                assign_id=assign_id)
        except Course.DoesNotExist or Assignment.DoesNotExist:
            raise Http404

        if request.user not in curr_course.instructors.all():
            return Response({'message': 'You are not allowed for this operation.'}, status=status.HTTP_403_FORBIDDEN)

        if curr_assign.current_status == 'set_outline':
            return Response({'message': 'You are not allowed for this operation unless you set the outline.'}, status=status.HTTP_403_FORBIDDEN)

        if curr_assign.current_status == 'outline_set':
            print("$$$$$$$$$$$$$%%%%%%%%%%%%%")
            print(curr_assign.publish_date, timezone.now(),
                  curr_assign.submission_deadline)
            print(curr_assign.publish_date < timezone.now())
            if curr_assign.publish_date <= timezone.now() < curr_assign.submission_deadline:
                curr_assign.current_status = 'published'
                curr_assign.published_for_subs = True
                curr_assign.save()
                print(curr_assign.current_status)
                return Response({'message': 'Assignment published successfully.'}, status=status.HTTP_200_OK)
            return Response({'message': 'Current date is not in range [publish_date, submission_deadline), wait or update the deadline/publish_date.'}, status=status.HTTP_403_FORBIDDEN)

        return Response({'message': 'You cannot publish the assignment since it was published already.'}, status=status.HTTP_403_FORBIDDEN)


@ login_required
@ api_view(['GET', 'POST'])
def assignment_outline_detail(request, course_id, assign_id):
    if request.method == 'GET':
        try:
            curr_course = Course.objects.get(course_id=course_id)
            curr_assign = curr_course.authored_assignments.get(
                assign_id=assign_id)
        except Course.DoesNotExist or Assignment.DoesNotExist:
            raise Http404

        if request.user not in list(chain(curr_course.instructors.all(), curr_course.teaching_assistants.all(), curr_course.students.all())):
            return Response({'message': 'You are not allowed for this operation'}, status=status.HTTP_403_FORBIDDEN)
        questions = curr_assign.questions.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        print("###############################")
        print(request.data)
        try:
            curr_course = Course.objects.get(course_id=course_id)
            curr_assign = curr_course.authored_assignments.get(
                assign_id=assign_id)
        except Course.DoesNotExist or Assignment.DoesNotExist:
            raise Http404

        if request.user not in curr_course.instructors.all():
            return Response({'message': 'You are not allowed for this operation'}, status=status.HTTP_403_FORBIDDEN)

        if curr_assign.current_status not in ['subs_closed', 'method_selected', 'grading_started']:
            for question in curr_assign.questions.all():
                try:
                    question.delete()
                except:
                    return Response({'message': f'fatal error in deleting existing outline, try later'}, status=500)

            post_data = []
            for question in request.data:
                serializer = QuestionSerializer(data=question)
                if serializer.is_valid():
                    serializer.save(parent_assign=curr_assign)
                    post_data.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if len(post_data) > 0:
                if curr_assign.current_status == 'set_outline':
                    curr_assign.current_status = 'outline_set'
                    curr_assign.save()

            return Response(post_data, status=status.HTTP_201_CREATED)
        else:
            return Response({'Message': f'You cannot modify the outline now. The current status of assign is {curr_assign.current_status}'}, status=400)


class CourseCreateView(generics.CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsGlobalInstructor]

    def perform_create(self, serializer):
        serializer.save(
            instructors=[self.request.user],
            entry_key=''.join(
                [random.choice(string.ascii_letters + string.digits) for n in range(7)])
        )


class UpdateCourseMetadataView(generics.UpdateAPIView):
    queryset = CourseMetadata.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsInstructorForMetadata]
    serializer_class = CourseMetadataSerializer
    lookup_field = 'course_id'


class AddSingleUserView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]
    serializer_class = SingleUserSerializer
    queryset = Course.objects.all()

    def post(self, request, course_id, format=None):
        try:
            course = Course.objects.get(course_id=course_id)
        except Course.DoesNotExist:
            return Response({'message': 'The course does not exist'}, status=404)

        ser = SingleUserSerializer(data=request.data)
        if ser.is_valid():
            email = ser.data.get('email')
            name = ser.data.get('name')
            roll_no = ser.data.get('institute_id')
            notify = ser.data.get('notify')
            role = ser.data.get('role')
            string_role = {
                's': 'Student',
                't': 'Teaching Assistant',
                'i': 'Instructor'
            }

            try:
                user = SwagraderUser.objects.get(email=email)
                user.first_name = name
                user.institute_id = roll_no

                if role == 's':
                    course.students.add(user)
                elif role == 't':
                    course.teaching_assistants.add(user)
                elif role == 'i':
                    course.instructors.add(user)
                else:
                    return Response({'message': 'Malformed role input'}, status=400)
                course.save()
                user.save()

                if not Roster.objects.filter(user=user).exists():
                    Roster.objects.create(user=user, course=course)

                if notify:
                    from django.core.mail import send_mail
                    sub = "Added to " + course.course_number
                    body = "You are added to " + course.course_number + \
                        " by the course instructor as " + \
                        string_role[role] + ". Do not reply to this email."
                    send_mail(subject=sub, message=body, from_email='SwaGrader', recipient_list=[
                              email], fail_silently=False)

                return Response({'message': 'succesfully added to the course'}, status=200)

            except SwagraderUser.DoesNotExist:
                # create new user and handle the addition to the course here
                # return Response here as it is
                from django.utils.crypto import get_random_string

                name_split = name.split()
                fname = name_split[0]
                if len(name_split) >= 2:
                    lname = name_split[1]
                else:
                    lname = ""

                pwd = get_random_string(length=10, allowed_chars='abcdefghjkmnpqrstuvwxyz'
                                        'ABCDEFGHJKLMNPQRSTUVWXYZ'
                                        '23456789')
                user = SwagraderUser(
                    email=email, institute_id=roll_no, first_name=fname, last_name=lname)
                user.set_password(pwd)

                if role == 'i':
                    user.global_instructor_privilege = True
                    user.save()
                    course.instructors.add(user)
                elif role == 't':
                    user.global_ta_privilege = True
                    user.save()
                    course.teaching_assistants.add(user)
                elif role == 's':
                    user.save()
                    course.students.add(user)
                else:
                    return Response({'message': 'Malformed role input'}, status=400)

                course.save()
                Roster.objects.create(user=user, course=course)

                # notification to be sent regardless of the notify boolean
                from django.core.mail import send_mail
                sub = "Added to " + course.course_number
                body = "You are added to " + course.course_number + " by the course instructor as " + \
                    string_role[role] + ". Your account credentials are your email and password: " + \
                    pwd + ". This is a system generated email, please do not reply."
                send_mail(subject=sub, message=body, from_email='SwaGrader',
                          recipient_list=[email], fail_silently=False)

                return Response({'message': 'succesfully added to the course'}, status=200)

        return Response({'message': ser.errors}, status=400)


class RosterListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]
    queryset = Roster.objects.all()
    serializer_class = CourseRosterSerializer


class RosterDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructorForMetadata]
    queryset = Roster.objects.all()
    serializer_class = CourseRosterSerializer

    def perform_destroy(self, instance):
        course = instance.course
        user = instance.user
        course.instructors.remove(user)
        course.teaching_assistants.remove(user)
        course.students.remove(user)
        course.save()
        return super().perform_destroy(instance)


class RosterUpdateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructorForMetadata]

    def put(self, request, course_id, pk, format=None):
        try:
            course = Course.objects.get(course_id=course_id)
            roster = Roster.objects.get(id=pk)
            user = roster.user
            roles = request.data.get('roles', None)
            if roles:
                for role in roles:
                    if role == 'student':
                        course.students.add(user)
                    elif role == 'ta':
                        course.teaching_assistants.add(user)
                    elif role == 'instructor':
                        course.instructors.add(user)
                course.save()
            else:
                return Response({'message': 'Bad input, roles does not exist'}, status=400)

        except Course.DoesNotExist or Roster.DoesNotExist:
            return Response({'message': 'The roster or the course does not exist.'}, status=404)


class CourseInstructorDetailUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseDetailInstructorSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructor]
    lookup_field = 'course_id'


class AssignmentListView(generics.ListAPIView):
    serializer_class = AssignmentListCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'course_id'

    def get_queryset(self):
        course = get_object_or_404(Course, course_id=self.kwargs['course_id'])
        return course.authored_assignments.all()


class AssignmentDetailUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssignmentListCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorForMetadata]
    lookup_field = 'assign_id'

    def get_queryset(self):
        course = get_object_or_404(Course, course_id=self.kwargs['course_id'])
        return course.authored_assignments.all()

    def perform_update(self, serializer):
        from datetime import datetime
        publish_date = serializer.initial_data.get('publish_date', None)
        submission_deadline = serializer.initial_data.get(
            'submission_deadline', None)
        format = "%Y-%m-%dT%H:%M"

        published_for_subs = False
        # if datetime.strptime(publish_date, format) <= datetime.now() and datetime.now() < datetime.strptime(submission_deadline, format):
        #     published_for_subs = True

        curr_course = Course.objects.get(course_id=self.kwargs['course_id'])
        serializer.save(course=curr_course,
                        published_for_subs=published_for_subs)


class AssignmentCreateView(generics.CreateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentListCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorForMetadata]
    lookup_field = 'course_id'

    def perform_create(self, serializer):
        from datetime import datetime
        publish_date = serializer.initial_data.get('publish_date')
        submission_deadline = serializer.initial_data.get(
            'submission_deadline')
        format = "%Y-%m-%dT%H:%M"

        published_for_subs = False
        # if datetime.strptime(publish_date, format) <= datetime.now() and datetime.now() < datetime.strptime(submission_deadline, format):
        #     published_for_subs = True

        curr_course = Course.objects.get(course_id=self.kwargs['course_id'])
        serializer.save(course=curr_course,
                        published_for_subs=published_for_subs)


class GradingMethodSelection(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id, assign_id):
        print("$$$$$$$$$$$$")
        print(request.data)
        course = get_object_or_404(Course, course_id=course_id)
        assign = get_object_or_404(
            course.authored_assignments.all(), assign_id=assign_id)
        if not request.user in course.instructors.all():
            return Response({'message': 'only instructors are allowed for the operation'}, status=status.HTTP_403_FORBIDDEN)

        if assign.current_status in ['subs_closed', 'method_selected']:
            method = request.data.get('method', None)
            if method == None or not method in ['pg', 'ng']:
                return Response({'message': 'Bad input'}, status=400)

            assign.grading_methodology = method
            assign.current_status = 'method_selected'
            assign.save()
            return Response({'message': 'Method selected for grading.'}, status=200)
        else:
            return Response({'message': f'the current status is {assign.current_status}. You cannot select the grading method on this stage.'}, status=status.HTTP_403_FORBIDDEN)


@login_required
@api_view(['POST', 'GET'])
def stage_grading(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    FLOW = ['set_outline', 'outline_set', 'published',
            'subs_closed', 'method_selected', 'grading_started']
    User = get_user_model()
    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)
    if request.method == 'POST':
        if assign.current_status == 'method_selected':
            role = request.data.get('role', None)
            email = request.data.get('email', None)
            action = request.data.get('action', None)
            if role and email and action and role in ['s', 't', 'i'] and action in ['add', 'remove']:
                if assign.grading_methodology == 'pg':
                    pg_profile = assign.assignment_peergrading_profile.all()[0]
                    if role == 's':
                        if pg_profile.peergraders.all().filter(email=email).exists():
                            if action == 'add':
                                return Response({'message': 'Already Exists!'}, status=400)
                            else:
                                peergrader = User.objects.get(email=email)
                                pg_profile.peergraders.remove(peergrader)
                                return Response({'message': 'successfully removed!'}, status=200)
                        else:
                            return Response({'message': 'student does not exist in staging'}, status=404)

                    elif role == 't':
                        if pg_profile.ta_graders.all().filter(email=email).exists():
                            if action == 'add':
                                return Response({'message': 'Already Exists!'}, status=400)
                            else:
                                ta = User.objects.get(email=email)
                                pg_profile.ta_graders.remove(ta)
                                return Response({'message': 'successfully removed!'}, status=200)
                        else:
                            return Response({'message': 'ta does not exist in staging'}, status=404)

                    elif role == 'i':
                        if pg_profile.instructor_graders.all().filter(email=email).exists():
                            if action == 'add':
                                return Response({'message': 'Already Exists!'}, status=400)
                            else:
                                instructor = User.objects.get(email=email)
                                pg_profile.instructor_graders.remove(
                                    instructor)
                                return Response({'message': 'successfully removed!'}, status=200)
                        else:
                            return Response({'message': 'instructor does not exist in staging'}, status=404)
                else:
                    pass
            else:
                return Response({'message': 'Bad input.'}, status=400)
        else:
            return Response({'message': f'Assignment cannot be staged as the current status is {assign.current_status}.'}, status=403)

    else:
        if assign.current_status in FLOW[4:6]:
            if assign.grading_methodology == 'pg':
                pg_profile = assign.assignment_peergrading_profile.all()[0]
                pg = pg_profile.peergraders.all()
                tg = pg_profile.ta_graders.all()
                ig = pg_profile.instructor_graders.all()

                response = {}
                response['peergraders'] = StagingRosterSerializer(
                    pg, many=True).data
                response['ta_graders'] = StagingRosterSerializer(
                    tg, many=True).data
                response['in_graders'] = StagingRosterSerializer(
                    ig, many=True).data
                return Response(response, status=200)
            else:
                pass
        else:
            return Response({'message': f'Assignment cannot be staged as the current status is {assign.current_status}.'}, status=403)


@login_required
@api_view(['POST'])
def set_number_of_probes(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    FLOW = ['set_outline', 'outline_set', 'published',
            'subs_closed', 'method_selected', 'grading_started']
    User = get_user_model()
    if request.method == 'POST':
        if assign.current_status == 'method_selected':
            try:
                probes = int(request.data.get('probes'))
                if assign.assign_submissions.all().count() < probes:
                    return Response({'message': 'This assign does not have that many submissions'}, status=400)
                assign.assignment_peergrading_profile.all()[
                    0].n_probes = probes
                assign.assignment_peergrading_profile.all()[0].save()
                return Response({'message': "n_probes set"})
            except:
                return Response({'message': 'probes key not passed'}, status=400)
        else:
            return Response({'message': f'Not possible, current status of assign is {assign.current_status}'})


@login_required
@api_view(['GET'])
def start_grading(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)
    if assign.current_status == 'method_selected':
        # select probes by some logic, we define it later here, probes would be selected
        # Probe is more like a submission, Probe will have a grader, marks, rubrics
        if assign.grading_methodology == "pg":
            outline_with_rubrics = get_outline_with_rubrics(assign)
            probes = get_probes(outline_with_rubrics, assign, 'random')
            if probes:
                assign.current_status == 'grading_started'
                assign.save()
                return Response(probes, status=200)
            else:
                return Response({"message": "Internal error in probe selection"}, status=500)

        elif assign.grading_methodology == "ng":
            return Response(status=200)

        else:
            return Response({'message': 'grading methodology must be either pg or ng'}, status=400)
    else:
        return Response({'message': f'Not possible, current status of assign is {assign.current_status}'})

##############################################################################################


@login_required
@api_view(['GET', 'POST'])
def global_rubric_create(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)

    if assign.current_status != 'set_outline':
        outline_with_rubrics = get_outline_with_rubrics(assign)
        if request.method == 'GET':
            return Response(outline_with_rubrics, status=200)
        if request.method == 'POST':
            sample_payload = {
                "questions": [
                    {
                        "qid": 23,
                        "max_marks": 30,
                        "min_marks": 0,
                        "rubrics": [
                            {
                                "marks": 10,
                                "description": "Step 1 is correct",
                            }
                        ],
                        "sub_questions": [
                            {
                                "sqid": 1,
                                "max_marks": 10,
                                "min_marks": 0,
                                "sub_rubrics": [
                                    {
                                        "marks": 10,
                                        "description": "Step 1 is correct",
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            questions = request.data.get("questions", None)
            # add sanatization check for questions
            for q in questions:
                qid = q['qid']
                rubrics = q['rubrics']
                max_marks = q['max_marks']
                min_marks = q['min_marks']
                sub_questions = q['sub_questions']
                ques = assign.questions.get(ques_id=qid)

                if rubrics:
                    try:
                        ques.g_rubrics.all().delete()
                        for r_data in rubrics:
                            desc = r_data.get('description', None)
                            marks = r_data.get('marks', None)
                            rub = GlobalRubric.objects.create(
                                description=desc, marks=marks, question=ques)
                    except:
                        return Response({"message": "Error in deletion of previous rubrics"}, status=500)
                else:
                    try:
                        ques.g_rubrics.all().delete()
                    except:
                        GlobalRubric.objects.create(
                            description="Correct", marks=max_marks, question=ques)
                        GlobalRubric.objects.create(
                            description="Incorrect", marks=min_marks, question=ques)

                for sq in sub_questions:
                    sqid = sq['sqid']
                    sub_rubrics = sq['sub_rubrics']
                    sq_max_marks = sq['max_marks']
                    sq_min_marks = sq['min_marks']
                    if sub_rubrics:
                        sub_ques = ques.sub_questions.get(sques_id=sqid)
                        try:
                            sub_ques.g_subrubrics.all().delete()
                            for sr_data in sub_rubrics:
                                desc = sr_data.get('description', None)
                                marks = sr_data.get('marks', None)
                                srub = GlobalSubrubric.objects.create(
                                    description=desc, marks=marks, sub_question=sub_ques)
                        except:
                            return Response({"message": "Error in deletion of previous sub_rubrics"}, status=500)
                    else:
                        GlobalSubrubric.objects.create(
                            description="Correct", marks=sq_max_marks, sub_question=ques)
                        GlobalSubrubric.objects.create(
                            description="Incorrect", marks=sq_min_marks, sub_question=ques)
            assign.current_status = 'rubric_set'
            assign.save()
            print(assign.current_status)
            return Response({'message': 'rubric_set'})

    else:
        return Response({'message': f'Not possible, current status of assign is {assign.current_status}'})


@login_required
@api_view(['GET'])
def get_probes_to_check(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    if not request.user in chain(course.teaching_assistants.all(), course.instructors.all()):
        return Response({'message': 'You are not allowed for this operation because you are not an instructor/ta'}, status=403)
    if assign.current_status not in ['rubric_set', 'papers_distributed']:
        return Response({'message': 'This step is not activated'}, status=403)
    probes_to_check = request.user.probes_to_check.all()
    probe_ids = []
    for p in probes_to_check:
        probe_ids.append(p.probe_id)
    return Response(probe_ids, status=200)


@login_required
@api_view(['GET', 'POST'])
def grade_probe(request, course_id, assign_id, probe_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    if not request.user in chain(course.teaching_assistants.all(), course.instructors.all()):
        return Response({'message': 'You are not allowed for this operation because you are not an instructor/ta'}, status=403)

    if assign.current_status not in ['rubric_set', 'papers_distributed']:
        return Response({'message': 'This step is not activated'}, status=403)
    probe = get_object_or_404(
        ProbeSubmission, probe_id=probe_id)
    if probe.probe_grader != request.user:
        return Response({'message': 'this probe id does not belong to you'})
    if request.method == 'GET':
        # give back the details for the assign, which is essentially the outline, and the global rubrics which are set for this assign
        outline_with_rubrics = get_outline_with_rubrics(
            assign)  # bug- sent probe instead of assign
        return Response(outline_with_rubrics, status=200)

    elif request.method == 'POST':
        # payload will be like
        sample_payload = {
            "questions": [
                {
                    "qid": 23,
                    "max_marks": 30,
                    "min_marks": 0,
                    "rubrics": [
                        {
                            "rubric_id": 1,
                            "marks": 10,
                            "description": "Step 1 is correct"
                        }
                    ],
                    "comment": {
                        "marks": None,
                        "description": None,
                    },
                    "sub_questions": [
                        {
                            "sqid": 1,
                            "max_marks": 10,
                            "min_marks": 0,
                            "sub_rubrics": [
                                {
                                    "sub_rubric_id": 1,
                                    "marks": 10,
                                    "description": "Step 1 is correct",
                                }
                            ],
                            "comment": {
                                "marks": None,
                                "description": None,
                            }
                        }
                    ]
                }
            ]
        }
        questions = request.data.get("questions", None)

        # check for payload sanitization
        # sanitization_status = sanitization_check(assign, questions)
        sanitization_status = 'ok'
        if sanitization_status == 'ok':
            for q in questions:
                qid = q['qid']
                rubrics = q['rubrics']
                max_marks = q['max_marks']
                min_marks = q['min_marks']
                sub_questions = q['sub_questions']
                comment = q['comment']
                ques = assign.questions.get(ques_id=qid)
                cur_ques = Question.objects.get(ques_id=q['qid'])
                sub = probe.parent_sub
                ques_sub = sub.submissions.all().get(question=cur_ques)
                probe_qsub = get_object_or_404(
                    probe.probe_questions.all(), parent_ques=ques_sub)
                if comment['marks'] != None:
                    # foriegn key not matching   probe_submission.probe_questions

                    try:
                        probe_qsub.comment.delete()
                        ProbeSubmissionQuestionComment.objects.create(
                            parent_ques=probe_qsub, marks=comment['marks'], comment=comment['description'])
                    except:
                        return Response({"message": "Error in deletion of comment"}, status=500)
                if rubrics:
                    try:
                        for r_data in rubrics:
                            desc = r_data.get('description', None)
                            marks = r_data.get('marks', None)
                            r_id = r_data.get('rubric_id')
                            probe_qsub.rubric = GlobalRubric.objects.get(
                                rubric_id=r_id)
                            probe_qsub.save()
                    except:
                        return Response({"message": "rubric didn't linked"}, status=500)

                for sq in sub_questions:
                    sqid = sq['sqid']
                    sub_rubrics = sq['sub_rubrics']
                    sq_max_marks = sq['max_marks']
                    sq_min_marks = sq['min_marks']
                    if sub_rubrics:
                        sub_ques = ques.sub_questions.get(sques_id=sqid)
                        try:
                            for sr_data in sub_rubrics:
                                desc = sr_data.get('description', None)
                                marks = sr_data.get('marks', None)
                                sub_rubric_id = sr_data.get('sub_rubric_id')
                                probe_sq_sub = probe_qsub.probe_subquestions.get(
                                    parent_probe_ques=probe_qsub, parent_sub_ques=sqid)
                                probe_sq_sub.sub_rubric = GlobalSubrubric.objects.get(
                                    sub_rubric_id=sub_rubric_id)
                                probe_sq_sub.save()
                        except:
                            return Response({"message": "sub-rubric didn't attatch"}, status=500)
                    return Response({"message": "grades submitted"}, status=200)
        else:
            return Response({"message": sanitization_status}, status=400)


@login_required
@api_view(['GET'])
def start_peergrading(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    FLOW = ['set_outline', 'outline_set', 'published',
            'subs_closed', 'method_selected', 'grading_started']
    User = get_user_model()
    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)

    if assign.current_status != 'rubric_set':
        return Response({'message': 'rubric must be set'}, status=403)

    pg_profile = assign.assignment_peergrading_profile.all()[0]
    peerdist = pg_profile.peerdist
    students = pg_profile.peergraders.all().order_by('email')
    papers = assign.assign_submissions.all().order_by('sub_id')
    probe_objects = ProbeSubmission.objects.all()
    probes = []
    for p in probe_objects:
        probes.append(p.parent_sub)
    print('$$$$$$$$$$$$$$$$$')
    P_papers = []
    NP_papers = []
    for p in papers:
        if p in probes:
            P_papers.append(p)
        else:
            NP_papers.append(p)

    P_students = []
    NP_students = []
    for p in papers:
        if p in probes:
            P_students.append(
                get_object_or_404(User, email=p.author.email))
        else:
            NP_students.append(
                get_object_or_404(User, email=p.author.email))
    # order of paper and students is maintained since we used same if condition in loops above
    print('probes', probes)
    print('p_papers', len(P_papers), P_papers)
    print('np_papers', len(NP_papers), NP_papers)
    student_paper_pair = match_making(
        P_papers, NP_papers, P_students, NP_students, peerdist)

    for sp in student_paper_pair:
        PeerGraders.objects.create(student=sp[0], paper=sp[1])
        print(sp[0], sp[1])

    # create peersubmissionquestion objects for all students,paper pairs
    outline_with_rubrics = get_outline_with_rubrics(assign)
    for pg in PeerGraders.objects.all():
        for q in outline_with_rubrics:
            cur_ques = Question.objects.all().get(ques_id=q['qid'])
            sub = pg.paper
            ques_sub = sub.submissions.all().get(question=cur_ques)
            psq = PeerSubmissionQuestion.objects.create(
                parent_ques=ques_sub, parent_tuple=pg)
            for sq in q['sub_questions']:
                sub_ques = SubQuestion.objects.get(sques_id=sq['sqid'])
                pssq = PeerSubmissionSubquestion.objects.create(
                    parent_peer_ques=psq, parent_sub_ques=sub_ques)

    assign.current_status = 'papers_distributed'
    assign.save()
    return Response({'message': 'Peer - Grading started'}, status=200)


@login_required
@api_view(['GET'])
def get_peer_papers(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    if not request.user in course.students.all():
        return Response({'message': 'You are not allowed for this operation because you are not an student'}, status=403)
    if request.method == 'GET':
        papers = PeerGraders.objects.all().filter(student=request.user)
        papers_of_current_assign = []
        for p in papers:
            if p.paper.assignment.assign_id == assign.assign_id:  # check if fk return obj or attribute
                papers_of_current_assign.append(p)
        if len(papers_of_current_assign) == 0:
            return Response({'message': 'no papers found'}, status=403)
        res = []
        for paper in papers_of_current_assign:
            serializer = PeerGradersSerializer(paper)
            content = JSONRenderer().render(serializer.data)
            res.append(content)
        return Response(res, status=200)


@csrf_exempt
@login_required
@api_view(['GET', 'POST'])
def grade_peer(request, course_id, assign_id, paper_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    if not request.user in course.students.all():
        print("usr forb")
        return Response({'message': 'You are not allowed for this operation because you are not an student'}, status=403)
    # probe_selected which status
    # if assign.current_status != 'papers_distributed':
    #     print("here forb")
    #     return Response({'message': 'This step is not activated'}, status=403)

    cur_paper = AssignmentSubmission.objects.get(sub_id=paper_id)
    pg = PeerGraders.objects.all().get(student=request.user, paper=cur_paper)
    peer_grader_obj = get_object_or_404(
        PeerGraders.objects.all(), student=request.user, paper=cur_paper)  # check how to give pk
    print("atleast this")
    if request.method == 'GET':
        print("atleast this")
        # give back the details for the assign, which is essentially the outline, and the global rubrics which are set for this assign
        outline_with_rubrics = get_outline_with_rubrics(assign)
        return Response(outline_with_rubrics, status=200)

    if request.method == 'POST':
        print("#############################")
        pg_profile = assign.assignment_peergrading_profile.all()[0]
        # user must not cross deadline
        if pg_profile.peergrading_deadline < timezone.now():
            return Response({'message': 'deadline over'})
        questions = request.data.get("questions", None)
        print(questions)
        # check for payload sanitization
        # sanitization_status = sanitization_check(assign, questions)
        sanitization_status = 'ok'
        if sanitization_status == 'ok':
            for q in questions:
                qid = q['qid']
                rubrics = q['rubrics']
                max_marks = q['max_marks']
                min_marks = q['min_marks']
                sub_questions = q['sub_questions']
                ques = Question.objects.get(ques_id=qid)
                cur_ques = Question.objects.get(ques_id=qid)
                ques_sub = cur_paper.submissions.all().get(question=cur_ques)
                peer_qsub = get_object_or_404(
                    pg.question_submissions.all(), parent_ques=ques_sub)
                if rubrics:
                    try:
                        for r_data in rubrics:
                            desc = r_data.get('description', None)
                            marks = r_data.get('marks', None)
                            r_id = r_data.get('rubric_id')
                            peer_qsub.rubric = GlobalRubric.objects.get(
                                rubric_id=r_id)
                            peer_qsub.save()
                    except:
                        return Response({"message": "rubric didn't linked"}, status=500)

                for sq in sub_questions:
                    sqid = sq['sqid']
                    sub_rubrics = sq['sub_rubrics']
                    sq_max_marks = sq['max_marks']
                    sq_min_marks = sq['min_marks']
                    if sub_rubrics:
                        sub_ques = ques.sub_questions.get(sques_id=sqid)
                        try:
                            for sr_data in sub_rubrics:
                                desc = sr_data.get('description', None)
                                marks = sr_data.get('marks', None)
                                sub_rubric_id = sr_data.get('sub_rubric_id')
                                peer_sq_sub = peer_qsub.peer_subquestions.get(
                                    parent_sub_ques=sub_ques)
                                peer_sq_sub.sub_rubric = GlobalSubrubric.objects.get(
                                    sub_rubric_id=sub_rubric_id)
                                peer_sq_sub.save()
                        except:
                            return Response({"message": "sub-rubric didn't attatch"}, status=500)

                    return Response({"message": peer_sq_sub.peer_subques_id}, status=200)
        else:
            return Response({"message": sanitization_status}, status=400)


@login_required
@api_view(['GET'])
def calculate_scores(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    pg_profile = assign.assignment_peergrading_profile.all()[0]
    #############################################################
    #############################################################
    ############################################################
    # if pg_profile.peergrading_deadline < datetime.now():
    #     return Response({'message': 'wait for deadline to be finished'})
    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)

    pg_profile = assign.assignment_peergrading_profile.all()[0]
    peerdist = pg_profile.peerdist
    students = pg_profile.peergraders.all().order_by('email')
    papers = assign.assign_submissions.all().order_by('sub_id')
    probe_objects = ProbeSubmission.objects.all()
    probes = []
    for p in probe_objects:
        probes.append(p.parent_sub)
    print('###############$$$$$$$$$')
    P_papers = []
    NP_papers = []
    for p in papers:
        if p in probes:
            P_papers.append(p)
        else:
            NP_papers.append(p)

    P_students = []
    NP_students = []
    for p in papers:
        if p in probes:
            P_students.append(
                get_object_or_404(User, email=p.author.email))
        else:
            NP_students.append(
                get_object_or_404(User, email=p.author.email))
    # order of paper and students is maintained since we used same if condition in loops above
    print('probes', probes)
    print('p_papers', len(P_papers), P_papers)
    print('np_papers', len(NP_papers), NP_papers)

    p_len = len(P_papers)
    np_len = len(NP_papers)
    num_ques = assign.questions.all().count()

    scores = [[[] for x in range(p_len+np_len)] for y in range(p_len+np_len)]
    stu_row = []
    paper_col = []
    question_seq = []
    probe_scores = []

    for p in P_papers:
        paper_col.append(p)
    for p in NP_papers:
        paper_col.append(p)
    for p in P_students:
        stu_row.append(p)
    for p in NP_students:
        stu_row.append(p)

    for i, grader in enumerate(stu_row):
        for j, paper in enumerate(paper_col):
            try:
                gp = PeerGraders.objects.get(student=grader, paper=paper)
                ques_subs = gp.question_submissions.all().order_by('peer_ques_id')
                for sub in ques_subs:
                    if len(question_seq) < num_ques:
                        question_seq.append(sub.parent_ques.question)
                    if sub.rubric:
                        scores[i][j].append(sub.rubric.marks)
                    else:
                        marks = 0.0
                        for subq_sub in sub.peer_subquestions.all():
                            marks += subq_sub.sub_rubric.marks
                        scores[i][j].append(marks)
            except:
                continue

    for s in scores:
        print(s)

    score_matrices = []

    for i in range(num_ques):
        mat = []
        for j in scores:
            mat.append([])
            for k in j:
                if len(k) == 0:
                    mat[-1].append(None)
                else:
                    mat[-1].append(k[i])
        score_matrices.append(mat)
    for mat in score_matrices:
        for i in mat:
            print(i)
        print()
    print(question_seq)

    for p in P_papers:
        ps = p.probe_submission.all()[0]
        psq = ps.probe_questions.all()
        print('psq', psq)
        lst = []
        for q in question_seq:
            for x in psq:
                print(x.parent_ques.question)
            probe_ques = [x for x in psq if x.parent_ques.question == q]
            probe_ques = probe_ques[0]
            if probe_ques.rubric:
                lst.append(probe_ques.rubric.marks)
            else:
                marks = 0.0
                for probe_subques in probe_ques.probe_subquestions.all():
                    marks += probe_subques.sub_rubric.marks
                lst.append(marks)

        probe_scores.append(lst)

    for i, ques in enumerate(question_seq):
        probe_score = []
        for ps in probe_scores:
            probe_score.append(ps[i])
        grades = trupeqa(
            score_matrices[i], pg_profile.param_mu, pg_profile.param_gm, pg_profile.n_probes, probe_score, pg_profile.alpha)
        for j in range(len(grades)):
            grader = stu_row[j]
            grade = grades[j]
            # bon = bonus[j]
            mrks = Marks.objects.create(
                student=grader, marks=grade, parent_assign=assign, bonus=0, total_marks=grade+0, ques=ques)

        for i in range(len(grades)):
            print('paper ', paper_col[i], 'got ', grades[i], ' marks')
        # for i in range(len(bonus)):
        #     print('student ', stu_row[i], 'got ', bonus[i], ' bonus')

    assign.current_status = 'grading_ended'
    assign.save()

    return Response({'message': 'ran good'})


@login_required
@api_view(['GET'])
def calculate_bonus(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    #############################################################
    #############################################################
    ############################################################
    # if pg_profile.peergrading_deadline < datetime.now():
    #     return Response({'message': 'wait for deadline to be finished'})
    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)

    pg_profile = assign.assignment_peergrading_profile.all()[0]
    peerdist = pg_profile.peerdist
    students = pg_profile.peergraders.all().order_by('email')
    papers = assign.assign_submissions.all().order_by('sub_id')
    probe_objects = ProbeSubmission.objects.all()
    probes = []
    for p in probe_objects:
        probes.append(p.parent_sub)
    print('###############$$$$$$$$$')
    P_papers = []
    NP_papers = []
    for p in papers:
        if p in probes:
            P_papers.append(p)
        else:
            NP_papers.append(p)

    P_students = []
    NP_students = []
    for p in papers:
        if p in probes:
            P_students.append(
                get_object_or_404(User, email=p.author.email))
        else:
            NP_students.append(
                get_object_or_404(User, email=p.author.email))
    # order of paper and students is maintained since we used same if condition in loops above
    print('probes', probes)
    print('p_papers', len(P_papers), P_papers)
    print('np_papers', len(NP_papers), NP_papers)

    p_len = len(P_papers)
    np_len = len(NP_papers)
    num_ques = assign.questions.all().count()

    scores = [[[] for x in range(p_len+np_len)] for y in range(p_len+np_len)]
    stu_row = []
    paper_col = []
    question_seq = []
    probe_scores = []

    for p in P_papers:
        paper_col.append(p)
    for p in NP_papers:
        paper_col.append(p)
    for p in P_students:
        stu_row.append(p)
    for p in NP_students:
        stu_row.append(p)

    for i, grader in enumerate(stu_row):
        for j, paper in enumerate(paper_col):
            try:
                gp = PeerGraders.objects.get(student=grader, paper=paper)
                ques_subs = gp.question_submissions.all().order_by('peer_ques_id')
                for sub in ques_subs:
                    if len(question_seq) < num_ques:
                        question_seq.append(sub.parent_ques.question)
                    if sub.rubric:
                        scores[i][j].append(sub.rubric.marks)
                    else:
                        marks = 0.0
                        for subq_sub in sub.peer_subquestions.all():
                            marks += subq_sub.sub_rubric.marks
                        scores[i][j].append(marks)
            except:
                continue

    for s in scores:
        print(s)

    score_matrices = []

    for i in range(num_ques):
        mat = []
        for j in scores:
            mat.append([])
            for k in j:
                if len(k) == 0:
                    mat[-1].append(None)
                else:
                    mat[-1].append(k[i])
        score_matrices.append(mat)
    for mat in score_matrices:
        for i in mat:
            print(i)
        print()
    print(question_seq)

    for p in P_papers:
        ps = p.probe_submission.all()[0]
        psq = ps.probe_questions.all()
        print('psq', psq)
        lst = []
        for q in question_seq:
            for x in psq:
                print(x.parent_ques.question)
            probe_ques = [x for x in psq if x.parent_ques.question == q]
            probe_ques = probe_ques[0]
            if probe_ques.rubric:
                lst.append(probe_ques.rubric.marks)
            else:
                marks = 0.0
                for probe_subques in probe_ques.probe_subquestions.all():
                    marks += probe_subques.sub_rubric.marks
                lst.append(marks)

        probe_scores.append(lst)

    for i, ques in enumerate(question_seq):
        probe_score = []
        for ps in probe_scores:
            probe_score.append(ps[i])
        yj =[]
        for cnt,pap in paper_col:
            stu = pap.author
            mti = Marks.objects.all().filter(ques = ques).filter(student = stu)[0]
            yj.append(mti.marks)

        bonus = calculate_bonus(
            score_matrices[i], pg_profile.param_mu, pg_profile.param_gm, pg_profile.n_probes, probe_score,yj, pg_profile.alpha)
        for j in range(len(bonus)):
            grader = stu_row[j]
            # grade = grades[j]
            bon = bonus[j]
            mti = Marks.objects.all().filter(student = grader).filter(ques = ques)[0]
            mti.bonus = bon
            mti.total_marks = mti.marks + mti.bonus
            mti.save()
            

        # for i in range(len(grades)):
        #     print('paper ', paper_col[i], 'got ', grades[i], ' marks')
        for i in range(len(bonus)):
            print('student ', stu_row[i], 'got ', bonus[i], ' bonus')

    assign.current_status = 'grading_ended'
    assign.save()

    return Response({'message': 'ran good'})



@login_required
@api_view(['GET'])
def regrading_requests(request, course_id, assign_id, ques_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    if not request.user in course.student.all():
        return Response({'message': 'You are not allowed for this operation because you are not an student'}, status=403)

    if assign.current_status != 'grading_ended':
        return Response({'message': 'You are not allowed for this operation because grading not yet ended'}, status=403)

    if assign.regrading_requests_deadline < datetime.datetime.now():
        return Response({'message': 'regrading request deadlilne exceeded'}, status=403)
    ques = Question.objects.all().filter(ques_id=ques_id)[0]
    marks_table_instance = Marks.objects.all().filter(
        student=request.user).filter(ques=ques)[0]
    marks_table_instance.regrade = 1
    marks_table_instance.save()

    return Response({'message': "submitted for regrading"}, status=200)


@login_required
@api_view(['GET'])
def assign_regraders(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)

    if assign.current_status != 'grading_ended':
        return Response({'message': 'You are not allowed for this operation because grading not yet ended'}, status=403)

    if assign.regrading_requests_deadline > datetime.datetime.now():
        return Response({'message': 'regrading request deadlilne not exceeded'}, status=403)

    marks_table_instances = Marks.objects.all().filter(regrade=1)
    ta = assign.assignment_peergrading_profile.ta_graders
    ins = assign.assignment_peergrading_profile.instructor_graders
    graders = list(chain(ta, ins))
    g_len = len(graders)
    for cnt, mti in enumerate(marks_table_instances):
        mti.regrader = graders[cnt % g_len]
        mti.save()

    return Response({'message': "regraders assigned"})


@login_required
@api_view(['GET'])
def get_regrading_questions(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    if not list(chain(request.user in course.instructors.all(), course.teaching_assistants.all())):
        return Response({'message': 'You are not allowed for this operation because you are not an instructor or teaching assistant'}, status=403)

    if assign.current_status != 'grading_ended':
        return Response({'message': 'You are not allowed for this operation because grading not yet ended'}, status=403)

    if assign.regrading_requests_deadline > datetime.datetime.now():
        return Response({'message': 'regrading request deadlilne not exceeded'}, status=403)

    marks_table_instances = request.user.get_regrading_ques
    marks_table_instances = marks_table_instances.filter(
        parent_assign=assign).filter(regrade=1)
    if(len(marks_table_instances) == 0):
        return Response({'message': 'No regrading requests'})
    res = []

    for mti in marks_table_instances:
        ques = mti.ques
        student = mti.student
        m_id = mti.m_id
        marks = mti.marks
        assign_sub = AssignmentSubmission.objects.all().filter(
            author=student).filter(assignment=assign)[0]
        ques_sub = QuestionSubmission.all().filter(
            submission=assign_sub).filter(question=ques)[0]
        pdf = ques_sub.pdf
        dict = {
            "m_id": m_id,
            "curr_marks": marks,
            "pdf": pdf,
            "student": student,
        }
        res.append(dict)

    return Response({"regrading_requests":res}, status=200)

@login_required
@api_view(['POST'])
def regrade(request, course_id, assign_id,m_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    mti = Marks.objects.all().filter(m_id = m_id)[0]
    if request.user != mti.regrader:
        return Response({'message': 'you are not the regrader'},status=403)
    
    sample_incomint_data = {
        "marks" : 2,
    }
    new_marks = request.data.get("marks")
    mti.marks = new_marks
    mti.regrade = 0
    mti.save()
    return Response({"message":"marks submitted"},status=200)
    

@login_required
@api_view(['GET'])
def get_marks(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)

    if assign.current_status != 'grading_ended':
        return Response({'message': 'You are not allowed for this operation because grading not yet ended'}, status=403)


@login_required
@api_view(['GET'])
def get_user_privilege(request, course_id):
    User = get_user_model()
    course = get_object_or_404(Course, course_id=course_id)
    if(request.user in course.instructors.all()):
        return Response({'privilege': 'instructor'})
    if(request.user in course.teaching_assistants.all()):
        return Response({'privilege': 'ta'})
    if(request.user in course.students.all()):
        return Response({'privilege': 'student'})
    else:
        return Response({'privilege': 'none'})


@api_view(['GET'])
def submit_assignment(request, course_id, assign_id):
    try:
        curr_course = Course.objects.get(course_id=course_id)
        curr_assign = curr_course.authored_assignments.get(assign_id=assign_id)
    except Course.DoesNotExist or Assignment.DoesNotExist:
        raise Http404

    return Response({'status': curr_assign.current_status})
