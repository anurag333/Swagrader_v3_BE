from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import *
from rest_framework.response import Response
from swagrader.settings import BASE_DIR
from django.http import HttpResponse, FileResponse, Http404
from django.views.decorators.clickjacking import xframe_options_exempt
from django.template import RequestContext
from django.template import Template
from rest_framework import serializers
from rest_framework.decorators import api_view


@api_view(['GET'])
def login_page(request):
    return render(request, 'login_page.html')


@api_view(['GET'])
def home(request):
    if request.user.global_instructor_privilege:
        return render(request, 'home_ins.html')
    if request.user.global_ta_privilege == True:
        return render(request, 'home_ta.html')
    return render(request, 'home_stu.html')


@api_view(['GET'])
def assign_list(request, course_id):
    course = Course.objects.get(course_id=course_id)
    context = {
        'course_id': course_id,
        'course_name': course.course_title,
    }
    return render(request, 'assign_list.html', context)


@api_view(['GET'])
@xframe_options_exempt
def assign_pdf(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    print(assign.current_status)
    if assign.current_status == 'set_outline' or assign.current_status == 'outline_set':
        return Response({'message': 'You are not allowed for this operation because assign not published'}, status=403)
    context = {
        'course_id': course_id,
        'assign_id': assign_id,
        'pdf': assign.pdf,
    }
    return render(request, 'assign_pdf.html', context)


@api_view(['GET'])
def peer_submission(request, course_id, assign_id, paper_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    if assign.current_status == 'set_outline' or assign.current_status == 'outline_set':
        return Response({'message': 'You are not allowed for this operation because assign not published'}, status=40)
    submission = AssignmentSubmission.objects.all().filter(sub_id=paper_id)[0]
    ques_subs = submission.submissions.all()
    ques_list = []
    ques_ids = []
    for sub in ques_subs:
        ques_list.append(sub.pdf)
        ques_ids.append(sub.question.ques_id)
    ques = zip(ques_list, ques_ids)
    context = {
        'course_id': course_id,
        'assign_id': assign_id,
        'pdf': assign.pdf,
        'paper_id': paper_id,
        'ques': ques,
    }

    return render(request, 'peer_submission.html', context)


@api_view(['GET'])
def probe_submission(request, course_id, assign_id, probe_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    # if assign.current_status == 'set_outline' or assign.current_status == 'outline_set':
    #     return Response({'message': 'You are not allowed for this operation because assign not published'}, status=40)
    submission = ProbeSubmission.objects.all().filter(
        probe_id=probe_id)[0].parent_sub
    ques_subs = submission.submissions.all()
    ques_list = []
    ques_ids = []
    for sub in ques_subs:
        ques_list.append(sub.pdf)
        ques_ids.append(sub.question.ques_id)
    ques = zip(ques_list, ques_ids)
    context = {
        'course_id': course_id,
        'assign_id': assign_id,
        'pdf': assign.pdf,
        'probe_id': probe_id,
        'ques': ques,
    }
    return render(request, 'probe_submission.html', context)


@api_view(['GET'])
def test(request):
    return Response({'message': 'lol'})

    class toySerializer(serializers.Serializer):
        message = serializers.CharField(max_length=200)

    class toy:
        def __init__(self, message):
            self.message = message

    return Response(toySerializer(toy('You are not allowed for this operation because assign not published')).data, status=200)
    return render(request, 'test.html')
