import re
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


@login_required
@api_view(['POST'])
def close_submissions(request, course_id, assign_id):
    if request.method == 'POST':
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
@api_view(['POST'])
def assignment_publish(request, course_id, assign_id):
    if request.method == 'POST':
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
            if curr_assign.publish_date <= timezone.now() < curr_assign.submission_deadline:
                curr_assign.current_status = 'published'
                curr_assign.published_for_subs = True
                curr_assign.save()
                print(curr_assign.status)
                return Response({'message': 'Assignment published successfully.'}, status=status.HTTP_200_OK)
            return Response({'message': 'Current date is not in range [publish_date, submission_deadline), wait or update the deadline/publish_date.'}, status=status.HTTP_403_FORBIDDEN)

        return Response({'message': 'You cannot publish the assignment since it was published already.'}, status=status.HTTP_403_FORBIDDEN)


@login_required
@api_view(['GET', 'POST'])
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
    permission_classes = [permissions.IsAuthenticated, IsInstructorForMetadata]
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
        course = get_object_or_404(Course, course_id=course_id)
        assign = get_object_or_404(
            Course.authored_assignments.all(), assign_id=assign_id)
        if not request.user in course.instructors.all():
            return Response({'message': 'only instructors are allowed for the operation'}, status=status.HTTP_403_FORBIDDEN)

        if assign.curr_status in ['subs_closed', 'method_selected']:
            method = request.data.get('method', None)
            if method == None or not method in ['pg', 'ng']:
                return Response({'message': 'Bad input'}, status=400)

            assign.grading_methodology = method
            assign.curr_status = 'method_selected'
            assign.save()
            return Response({'message': 'Method selected for grading.'}, status=200)
        else:
            return Response({'message': f'the current status is {assign.current_status}. You cannot select the grading method on this stage.'}, status=status.HTTP_403_FORBIDDEN)


@login_required
@api_view(['POST', 'GET'])
def stage_grading(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        Course.authored_assignments.all(), assign_id=assign_id)
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
                    pg_profile = assign.assignment_peergrading_profile
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
                pg_profile = assign.assignment_peergrading_profile
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
        Course.authored_assignments.all(), assign_id=assign_id)
    FLOW = ['set_outline', 'outline_set', 'published',
            'subs_closed', 'method_selected', 'grading_started']
    User = get_user_model()
    if request.method == 'POST':
        if assign.current_status == 'method_selected':
            try:
                probes = request.data.get('probes')
                if assign.assign_submissions.all().count() < probes:
                    return Response({'message': 'This assign does not have that many submissions'}, status=400)
                assign.assignment_peergrading_profile.n_probes = probes
                assign.assignment_peergrading_profile.save()
            except:
                return Response({'message': 'probes key not passed'}, status=400)
        return Response({'message': f'Not possible, current status of assign is {assign.current_status}'})


@login_required
@api_view(['POST'])
def start_grading(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        Course.authored_assignments.all(), assign_id=assign_id)
    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)

    if assign.current_status == 'method_selected':
        # select probes by some logic, we define it later here, probes would be selected
        # Probe is more like a submission, Probe will have a grader, marks, rubrics
        if assign.grading_methodology == "pg":

            subs = assign.assign_submissions.all()
            probes = get_probes(subs, method='random')
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


@login_required
@api_view(['GET', 'POST'])
def grade_probe_instructor(request, course_id, assign_id, probe_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        Course.authored_assignments.all(), assign_id=assign_id)

    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)

    if assign.current_status == 'probes_selected':
        return Response({'message': 'This step is not activated'}, status=403)

    probe = get_object_or_404(
        assign.assign_submissions.all(), probe_submission__probe_id=probe_id)
    if request.method == 'GET':
        # give back the details for the assign, which is essentially the outline, and the global rubrics which are set for this assign
        outline_with_rubrics = get_outline_with_rubrics(assign)  #bug- sent probe instead of assign
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
                            "marks": 10,
                            "description": "Step 1 is correct",
                            "selected": True
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
                                    "marks": 10,
                                    "description": "Step 1 is correct",
                                    "selected": False,
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
        questions = request.DATA.get("questions", None)

        # check for payload sanitization
        sanitization_status = sanitization_check(assign, questions)

        if sanitization_status == 'ok':
            for q in questions:
                qid = q['qid']
                rubrics = q['rubrics']
                max_marks = q['max_marks']
                min_marks = q['min_marks']
                sub_questions = q['sub_questions']
                comment = q['comment']
                ques = assign.questions.get(ques_id=qid)

                if comment['marks'] != None:
                    # foriegn key not matching   probe_submission.probe_questions
                    probe_qsub = get_object_or_404(
                        probe.probe_questions.all(), parent_ques__ques_id=qid)
                    try:
                        probe_qsub.comment.delete()
                        ProbeSubmissionQuestionComment.objects.create(
                            parent_ques=probe_qsub, marks=comment['marks'], comment=comment['description'])
                    except:
                        return Response({"message": "Error in deletion of comment"}, status=500)
                if rubrics:
                    try:
                        ques.g_rubrics.all().delete()
                        for r_data in rubrics:
                            desc = r_data.get('description', None)
                            marks = r_data.get('marks', None)
                            rub = GlobalRubric.objects.create(
                                description=desc, marks=marks, question=ques)

                            if r_data['selected']:
                                rub.probe_rubric.selected = True
                                rub.save()
                    except:
                        return Response({"message": "Error in deletion of previous rubrics"}, status=500)
                else:
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
                                if sr_data['selected']:
                                    srub.probe_subrubric.selected = True
                                    srub.save()
                        except:
                            return Response({"message": "Error in deletion of previous sub_rubrics"}, status=500)
                    else:
                        GlobalSubrubric.objects.create(
                            description="Correct", marks=sq_max_marks, sub_question=ques)
                        GlobalSubrubric.objects.create(
                            description="Incorrect", marks=sq_min_marks, sub_question=ques)
        else:
            return Response({"message": sanitization_status}, status=400)




##############################################################################################

@login_required
@api_view(['GET', 'POST'])
def grade_probe_ta(request, course_id, assign_id, probe_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        Course.authored_assignments.all(), assign_id=assign_id)

    if not request.user in course.teaching_assistants.all():
        return Response({'message': 'You are not allowed for this operation because you are not an teaching assistant'}, status=403)
    # probe_selected which status
    if assign.current_status == 'probes_selected':
        return Response({'message': 'This step is not activated'}, status=403)

    probe = get_object_or_404(
        assign.assign_submissions.all(), probe_submission__probe_id=probe_id)
    if request.method == 'GET':
        # give back the details for the assign, which is essentially the outline, and the global rubrics which are set for this assign
        outline_with_rubrics = get_outline_with_rubrics(assign)   
        return Response(outline_with_rubrics, status=200)

    elif request.method == 'POST':
        questions = request.DATA.get("questions", None)

        # check for payload sanitization
        sanitization_status = sanitization_check(assign, questions)

        if sanitization_status == 'ok':
            for q in questions:
                qid = q['qid']
                rubrics = q['rubrics']
                max_marks = q['max_marks']
                min_marks = q['min_marks']
                sub_questions = q['sub_questions']
                comment = q['comment']
                ques = assign.questions.get(ques_id=qid)

                if comment['marks'] != None:
                    # foriegn key not matching   probe_submission.probe_questions
                    probe_qsub = get_object_or_404(
                        probe.probe_questions.all(), parent_ques__ques_id=qid)
                    try:
                        probe_qsub.comment.delete()
                        ProbeSubmissionQuestionComment.objects.create(
                            parent_ques=probe_qsub, marks=comment['marks'], comment=comment['description'])
                    except:
                        return Response({"message": "Error in deletion of comment"}, status=500)
                # deleted rubric part

                for sq in sub_questions:
                    sqid = sq['sqid']
                    sub_rubrics = sq['sub_rubrics']
                    sq_max_marks = sq['max_marks']
                    sq_min_marks = sq['min_marks']
                    # deleted subrubric part
        else:
            return Response({"message": sanitization_status}, status=400)


@login_required
@api_view(['GET'])
def start_peergrading(request, course_id, assign_id):
    # distribute, create all profiles and rubrics, and action!
    # The idea is to use the DAGs for the problem and then see what can be done for that for the cause in the problem for that
    # So for this we will start with the fact that we cannot create a loop < n-k+1 length in this
    # Lets try to create a mock example for this and later we will essentially do this for all the questions (np)
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        Course.authored_assignments.all(), assign_id=assign_id)
    FLOW = ['set_outline', 'outline_set', 'published',
            'subs_closed', 'method_selected', 'grading_started']
    User = get_user_model()
    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)

    if assign.current_status != 'method_selected':
        return Response({'message': 'Grading method must be selected'}, status=403)

    pg_profile = assign.assignment_peergrading_profile
    peerdist = pg_profile.peerdist
    students = pg_profile.peergraders.all()
    papers = assign.assign_submissions.all()
    probe_objects = ProbeSubmission.objects.all()
    probes = []
    for p in probe_objects:
        probes.append(p.sub_id)

    P_papers = []
    NP_papers = []
    for p in papers:
        if p.sub_id in probes:
            P_papers.append(p)
        else:
            NP_papers.append(p)

    P_students = []
    NP_students = []

    for p in papers:
        if p.sub_id in probes:
            P_students.append(
                SwagraderUser.objects.all().filter(email=p.author))
        else:
            NP_students.append(
                SwagraderUser.objects.all().filter(email=p.author))
    # order of paper and students is maintained since we used same if condition in loops above
    student_paper_pair = match_making(
        P_papers, NP_papers, P_students, NP_students, peerdist)

    for sp in student_paper_pair:
        PeerGraders.objects.create(Student=sp[0], paper=sp[1])

    # create peersubmissionquestion objects for all students,paper pairs

    assign.current_status = 'grading_started'
    assign.save()
    return Response({'message': 'Grading started'}, status=200)


@login_required
@api_view(['GET'])
def get_peer_papers(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        Course.authored_assignments.all(), assign_id=assign_id)
    if not request.user in course.students.all():
        return Response({'message': 'You are not allowed for this operation because you are not an student'}, status=403)
    if request.method == 'GET':
        papers = PeerGraders.objects.all().filter(email=request.user.email)
        papers_of_current_assign = []
        for p in papers:
            if p.assignment.assign_id == assign.assign_id:  # check if fk return obj or attribute
                papers_of_current_assign.append(p)
        if len(papers_of_current_assign) == 0:
            return Response({'message': 'no papers found'}, status=403)
        return Response(papers_of_current_assign, status=200)




@login_required
@api_view(['GET', 'POST'])
def grade_peer(request, course_id, assign_id, peer_id,paper_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        Course.authored_assignments.all(), assign_id=assign_id)

    if not request.user in course.students.all():
        return Response({'message': 'You are not allowed for this operation because you are not an student'}, status=403)
    # probe_selected which status
    if assign.current_status != 'grading_started':
        return Response({'message': 'This step is not activated'}, status=403)

    peer_grader_obj = get_object_or_404(
        PeerGraders.objects.all(), student=peer_id,paper = paper_id)  #check how to give pk
    if request.method == 'GET':
        # give back the details for the assign, which is essentially the outline, and the global rubrics which are set for this assign
        outline_with_rubrics = get_outline_with_rubrics(assign)
        return Response(outline_with_rubrics, status=200)

    elif request.method == 'POST':
        pg_profile = assign.assignment_peergrading_profile
        # user must not cross deadline
        if pg_profile.peergrading_deadline < datetime.datetime.now():
            return Response({'message': 'deadline over'})
        questions = request.DATA.get("questions", None)

        # check for payload sanitization
        sanitization_status = sanitization_check(assign, questions)

        if sanitization_status == 'ok':
            for q in questions:
                qid = q['qid']
                rubrics = q['rubrics']
                max_marks = q['max_marks']
                min_marks = q['min_marks']
                sub_questions = q['sub_questions']
                
                ques = assign.questions.get(ques_id=qid)

                for sq in sub_questions:
                    sqid = sq['sqid']
                    sub_rubrics = sq['sub_rubrics']
                    sq_max_marks = sq['max_marks']
                    sq_min_marks = sq['min_marks']
                    # deleted subrubric part
        else:
            return Response({"message": sanitization_status}, status=400)



@login_required
@api_view(['GET'])
def calculate_bonus_and_scores(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        Course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    pg_profile = assign.assignment_peergrading_profile
    if pg_profile.peergrading_deadline < datetime.now():
        return Response({'message': 'wait for deadline to be finished'})
    if not request.user in course.instructors.all():
        return Response({'message': 'You are not allowed for this operation because you are not an instructor'}, status=403)

    pg_profile = assign.assignment_peergrading_profile
    peerdist = pg_profile.peerdist
    students = pg_profile.peergraders.all()
    papers = assign.assign_submissions.all()
    probe_objects = ProbeSubmission.objects.all()
    probes = []
    for p in probe_objects:
        probes.append(p.sub_id)

    P_papers = []
    NP_papers = []
    for p in papers:
        if p.sub_id in probes:
            P_papers.append(p)
        else:
            NP_papers.append(p)

    P_students = []
    NP_students = []

    for p in papers:
        if p.sub_id in probes:
            P_students.append(
                SwagraderUser.objects.all().filter(email=p.author))
        else:
            NP_students.append(
                SwagraderUser.objects.all().filter(email=p.author))


    questions = assign.questions.all()


    for ques in questions:
        for stu in students:
            

