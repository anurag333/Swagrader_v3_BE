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
from django.utils.timezone import timezone


class EnrollCourseView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EntryKeySerializer

    def post(self, request, format=None):
        ser = EntryKeySerializer(data=request.data)
        if ser.is_valid(raise_exception=True):
            course = get_object_or_404(
                Course, entry_key=ser.data.get('entry_key'))
            if course.entry_restricted:
                return Response({'message': 'Entry in this course is restricted'}, status=403)
            else:
                course.students.add(request.user)
                return Response({'message': 'Successfully added to the course.', 'course_id': course.course_id}, status=200)


class CourseDetailStudentView(generics.RetrieveAPIView):
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    lookup_field = 'course_id'


class QuestionListView(views.APIView):
    def get(self, request, course_id, assign_id):
        course = get_object_or_404(Course, course_id=course_id)
        if request.user not in course.students.all():
            return Response({'message': 'Only students of the course can access this API.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            assign = course.authored_assignments.get(assign_id=assign_id)
            if not assign.published_for_subs:
                return Response({'message': 'Assignment is not yet published, you cannot access the questions unless it is published by the instructor'}, status=status.HTTP_403_FORBIDDEN)

            questions = assign.questions.all()
            ser = QuestionListSerializer(questions, many=True)
            return Response(ser.data)

        except Assignment.DoesNotExist:
            return Response({'message': 'Assignment does not exist for this course.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST', 'GET'])
def submit_assignment(request, course_id, assign_id):
    try:
        curr_course = Course.objects.get(course_id=course_id)
        curr_assign = curr_course.authored_assignments.get(assign_id=assign_id)
    except Course.DoesNotExist or Assignment.DoesNotExist:
        raise Http404

    if request.user not in curr_course.students.all():
        return Response({'message': 'Only students are allowed to access the  API.'}, status=status.HTTP_403_FORBIDDEN)

    if not curr_assign.published_for_subs or curr_assign.current_status == 'set_outline' or curr_assign.current_status == 'outline_set':
        return Response({'message': 'Assignment not avaliable at the moment.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'POST':
        if not curr_assign.published_for_subs:
            return Response({'message': 'Assignment is not published for submissions.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            sub = AssignmentSubmission.objects.get(
                author=request.user, assignment=curr_assign)
        except AssignmentSubmission.DoesNotExist:
            sub = AssignmentSubmission.objects.create(
                author=request.user, assignment=curr_assign)

        for qid in request.data.keys():
            if not curr_assign.questions.filter(ques_id=qid).exists():
                return Response({'message': f'{qid} does not exist for this assignment, bad input.'}, status=status.HTTP_400_BAD_REQUEST)

        # payload: 'ques_id': <FILE>
        filename = ''.join(
            [random.choice(string.ascii_letters + string.digits) for n in range(7)])
        for ques_id in request.data.keys():
            print(ques_id)
            try:
                ques = curr_assign.questions.get(ques_id=ques_id)
                try:
                    qsub = ques.qsubmissions.get(
                        submission__author=request.user)
                    pdf = request.data[ques_id]
                    pdf = filename + '.pdf'
                    qsub.pdf = pdf
                    qsub.save()
                    print(qsub.pdf.path, " is the path")
                except QuestionSubmission.DoesNotExist:
                    qsub = QuestionSubmission.objects.create(
                        submission=sub, question=ques, pdf=request.data[ques_id])
            except Question.DoesNotExist:
                return Response({'message': f'{ques_id} does not exist for this assignment, bad input.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Submitted succesfully'}, status=200)

    elif request.method == 'GET':
        questions = curr_assign.questions.all()
        data = {}
        data['questions'] = []
        for question in questions:
            json = {}
            json['ques_id'] = question.ques_id
            json['sno'] = question.sno
            json['title'] = question.title
            # json['max_marks'] = question.max_marks
            json['pdf'] = ""
            if question.qsubmissions.filter(submission__author=request.user).exists():
                qsub = question.qsubmissions.get(
                    submission__author=request.user)
                json['pdf'] = qsub.pdf.url

            data['questions'].append(json)
        print(data)
        return Response(data=data, status=200)
