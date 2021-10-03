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
import datetime
from django.utils import timezone
from itertools import chain
from django import forms


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
    print(assign.publish_date, timezone.now())
    if(assign.publish_date < timezone.now()):
        print("aaya")
        if assign.current_status in ['outline_set', "set_outline"]:
            assign.current_status = 'published'
            assign.published_for_subs = True
            assign.save()

    last_date = assign.submission_deadline if not assign.allow_late_subs else assign.late_sub_deadline
    if timezone.now() > last_date and assign.current_status in ['set_outline', 'outline_set', 'published']:
        assign.current_status = "subs_closed"
        assign.save()

    if not request.user in chain(course.instructors.all(), course.teaching_assistants.all()):
        if assign.current_status == 'set_outline' or assign.current_status == 'outline_set':
            return render(request, 'error.html', {'message': 'You are not allowed for this operation because assign not published'})
    print("fe ===========++++++++", assign.current_status)
    probing_deadline = ""
    peergrading_deadline = ""
    try:
        pg_profile = assign.assignment_peergrading_profile.all()[0]
        probing_deadline = pg_profile.probing_deadline
        peergrading_deadline = pg_profile.peergrading_deadline
    except:
        pass

    class myform(forms.Form):
        question_feild = forms.CharField(max_length=100000)

    form1 = myform()
    context = {
        'course_id': course_id,
        'assign_id': assign_id,
        'pdf': assign.pdf,
        "assign_status": assign.current_status,
        "assign_name": assign.title,
        "probing_deadline": probing_deadline,
        "peergrading_deadline": peergrading_deadline,
        'form': form1,
    }
    return render(request, 'assign_pdf.html', context)


@api_view(['GET'])
def create_roster(request, course_id):
    class myform(forms.Form):
        question_feild = forms.CharField(max_length=100000)

    form1 = myform()
    course = get_object_or_404(Course, course_id=course_id)

    User = get_user_model()

    if request.user not in course.instructors.all():
        return render(request, 'error.html', {'message': 'you are not an student'})

    context = {
        'course_id': course.course_id,
        'course_name': course.course_title,
        'form': form1,
    }
    return render(request, 'create_roster.html', context)


@api_view(['GET'])
def create_assign_roster(request, course_id, assign_id):
    class myform(forms.Form):
        question_feild = forms.CharField(max_length=100000)

    form1 = myform()
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(Assignment, assign_id=assign_id)
    User = get_user_model()

    if request.user not in course.instructors.all():
        return render(request, 'error.html', {'message': 'you are not an instructor'})

    try:
        pg_profile = assign.assignment_peergrading_profile.all()[0]
    except:
        pg_profile = AssignmentPeergradingProfile.objects.create(
            assignment=assign)
        for stu in course.students.all():
            pg_profile.peergraders.add(stu)
        for ins in course.instructors.all():
            pg_profile.instructor_graders.add(ins)
        for ta in course.teaching_assistants.all():
            pg_profile.ta_graders.add(ta)

    context = {
        'course_id': course.course_id,
        'course_name': course.course_title,
        'assign_id': assign.assign_id,
        'form': form1,
    }
    return render(request, 'create_assign_roster.html', context)


@api_view(['GET'])
def fe_submit_assignment(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    if request.user not in course.students.all():
        return render(request, 'error.html', {'message': 'you are not an student'})

    if not (assign.current_status in ['published']):
        return render(request, 'error.html', {'message': 'assignment status is not published'})

    questions = assign.questions.all()
    print(questions)

    class myform(forms.Form):
        def __init__(self, questions, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for ques in questions:
                print(ques)
                self.fields[str(ques.ques_id)] = forms.FileField(
                    required=True)

    form1 = myform(questions)

    context = {
        'course_id': course.course_id,
        'course_name': course.course_title,
        'assign_id': assign.assign_id,
        'assign_name': assign.title,
        'form': form1,
    }
    return render(request, 'submit_assignment.html', context)


@api_view(['GET'])
def set_rubric(request, course_id, assign_id):
    class myform(forms.Form):
        question_feild = forms.CharField(max_length=100000)

    form1 = myform()
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    if request.user not in course.instructors.all():
        return render(request, 'error.html', {'message': 'you are not an instructor'})

    if not (assign.current_status in ['outline_set', 'published', 'subs_closed', 'method_selected']):
        return render(request, 'error.html', {'message': 'method cant be selected now'})
    context = {
        'course_id': course.course_id,
        'course_name': course.course_title,
        'assign_id': assign.assign_id,
        'assign_name': assign.title,
        'form': form1,
    }
    return render(request, 'set_rubric.html', context)


@api_view(['GET'])
def update_assign_details(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    if request.user not in course.instructors.all():
        return render(request, 'error.html', {'message': 'you are not an instructor'})

    if assign.current_status == 'set_outline' or assign.current_status == 'outline_set':
        return render(request, 'error.html', {'message': 'method cant be selected now'})
    context = {
        'course_id': course.course_id,
        'course_name': course.course_title,
        'assign_id': assign.assign_id,
        'assign_name': assign.title,
    }
    return render(request, 'update_assign_details.html', context)


@api_view(['GET'])
def fe_method_select(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    if request.user not in course.instructors.all():
        return render(request, 'error.html', {'message': 'you are not an instructor'})

    if not (assign.current_status == 'method_selected' or assign.current_status == 'subs_closed' or assign.current_status == 'rubric_set'):
        return render(request, 'error.html', {'message': 'method cant be selected now'})
    context = {
        'course_id': course.course_id,
        'course_name': course.course_title,
        'assign_id': assign.assign_id,
        'assign_name': assign.title,
    }
    return render(request, 'fe_method_select.html', context)


@api_view(['GET'])
def fe_set_outline(request, course_id, assign_id):
    class myform(forms.Form):
        question_feild = forms.CharField(max_length=100000)

    form1 = myform()

    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    if request.user not in course.instructors.all():
        return render(request, 'error.html', {'message': 'you are not an instructor'})

    if not (assign.current_status in ["set_outline", "outline_set", "published", "subs_closed", "method_selected"]):
        return render(request, 'error.html', {'message': 'Outline cannot be changed now'})
    context = {
        'course_id': course.course_id,
        'course_name': course.course_title,
        'assign_id': assign.assign_id,
        'assign_name': assign.title,
        'form': form1

    }
    return render(request, 'fe_set_outline.html', context)


@api_view(['GET'])
def peer_list(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    context = {
        'course_id': course_id,
        'assign_id': assign_id,
    }
    return render(request, 'peer_list.html', context)


@api_view(['GET'])
def peer_submission(request, course_id, assign_id, paper_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    submission = AssignmentSubmission.objects.all().filter(sub_id=paper_id)[0]
    ques_subs = submission.submissions.all()
    ques_list = []
    ques_ids = []
    ques_desc = []
    for sub in ques_subs:
        ques_ids.append(sub.question.ques_id)
        ques_list.append(sub.pdf)
        ques_desc.append(sub.question.description)
    ques = zip(ques_list, ques_ids, ques_desc)
    print(ques_list, ques_ids, ques_desc)

    class myform(forms.Form):
        question_feild = forms.CharField(max_length=100000)

    form1 = myform()

    context = {
        'course_id': course_id,
        'assign_id': assign_id,
        'pdf': assign.pdf,
        'paper_id': paper_id,
        'ques': ques,
        'form': form1,
    }

    return render(request, 'peer_submission.html', context)


@api_view(['GET'])
def probe_list(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    context = {
        'course_id': course_id,
        'assign_id': assign_id,
    }
    return render(request, 'probe_list.html', context)


@api_view(['GET'])
def probe_submission(request, course_id, assign_id, probe_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    print("len", len(
        ProbeSubmission.objects.all().filter(probe_id=probe_id)))
    submission = ProbeSubmission.objects.all().filter(
        probe_id=probe_id)[0].parent_sub
    probe = get_object_or_404(
        ProbeSubmission, probe_id=probe_id)
    print(probe.probe_id)
    ques_subs = submission.submissions.all()
    ques_list = []
    ques_ids = []
    ques_desc = []
    print("$$$$$$$$$$$$$$$$$$$$$$")
    for sub in ques_subs:
        print(sub.question.ques_id)
        ques_list.append(sub.pdf)
        ques_ids.append(sub.question.ques_id)
        ques_desc.append(sub.question.description)
    ques = zip(ques_list, ques_ids, ques_desc)

    class myform(forms.Form):
        question_feild = forms.CharField(max_length=100000)

    form1 = myform()

    context = {
        'course_id': course_id,
        'assign_id': assign_id,
        'pdf': assign.pdf,
        'probe_id': probe_id,
        'ques': ques,
        'form': form1,
    }
    return render(request, 'probe_submission.html', context)


@api_view(['GET'])
def calc_score(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    if assign.current_status != 'papers_distributed':
        return Response({'message': 'You are not allowed for this operation because assign not published'}, status=403)

    pg_profile = assign.assignment_peergrading_profile.all()[0]
    if timezone.now() < pg_profile.peergrading_deadline:
        pg_profile.peergrading_deadline = timezone.now()
        pg_profile.save()

    context = {
        'course_id': course_id,
        'assign_id': assign_id,
    }
    return render(request, 'calc_score.html', context)


@api_view(['GET'])
def set_regrading_deadline(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    if assign.current_status not in ['papers_distributed', 'regrading_req_start']:
        return Response({'message': 'You are not allowed for this at this point'}, status=403)

    pg_profile = assign.assignment_peergrading_profile.all()[0]

    context = {
        'course_id': course_id,
        'assign_id': assign_id,
    }
    return render(request, 'set_regrading_deadline.html', context)


@api_view(['GET'])
def fe_regrading_request(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    if assign.current_status != "regrading_req_start":
        return render(request, 'error.html', {'message': 'regrading not allowed'})
    if assign.regrading_requests_deadline == None:
        return render(request, "error.html", {'message': 'regrading request deadline not set by instructor'})

    if timezone.now() > assign.regrading_requests_deadline:
        return render(request, 'error.html', {'message': 'regrading deadline crossed'})
    pg_profile = assign.assignment_peergrading_profile.all()[0]

    user = request.user

    mtis = user.get_marks.all()
    print(len(mtis))
    ques = []
    for mti in mtis:
        print("mti", mti.student.email, mti.ques.ques_id,
              mti.marks, mti.m_id, mti.regrade)
        if mti.regrade == 1:
            ques.append(mti.ques.ques_id)

    print("ques", ques)
    if request.method == "GET":
        context = {
            'course_id': course_id,
            'assign_id': assign_id,
            'ques': ques,
        }
        return render(request, 'fe_regrading_request.html', context)


@api_view(['GET'])
def fe_regrading_request_papers(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    if assign.current_status != "start_regrading":
        return render(request, 'error.html', {'message': 'regrading not allowed'})
    if timezone.now() > assign.regrading_deadline:
        return render(request, 'error.html', {'message': 'regrading deadline crossed'})
    pg_profile = assign.assignment_peergrading_profile.all()[0]

    class myform(forms.Form):
        question_feild = forms.CharField(max_length=100000)

    form1 = myform()

    if request.method == "GET":
        context = {
            'course_id': course_id,
            'assign_id': assign_id,
            'form': form1,
        }
        return render(request, 'fe_regrading_request_papers.html', context)


@api_view(['GET'])
def select_ta(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()
    if assign.current_status != "rubric_set":
        return render(request, 'error.html', {'message': 'Not allowed'})
    pg_profile = assign.assignment_peergrading_profile.all()[0]

    if request.method == "GET":
        class myform(forms.Form):
            question_feild = forms.CharField(max_length=100000)

    form1 = myform()

    if request.method == "GET":
        context = {
            'course_id': course_id,
            'assign_id': assign_id,
            'form': form1,
        }
        return render(request, 'select_ta.html', context)


@api_view(['GET'])
def see_grades(request, course_id, assign_id):
    course = get_object_or_404(Course, course_id=course_id)
    assign = get_object_or_404(
        course.authored_assignments.all(), assign_id=assign_id)
    User = get_user_model()

    if assign.current_status not in ['bonus_calculated', 'regrading_req_start', 'start_regrading', 'grading_ended']:
        return Response({'message': 'You are not allowed for this operation'}, status=403)

    pg_profile = assign.assignment_peergrading_profile.all()[0]

    context = {
        'course_id': course_id,
        'assign_id': assign_id,
    }
    return render(request, 'see_grades.html', context)


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
