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

@api_view(['POST'])
def close_submissions(request, course_id, assign_id):
    if request.method == 'POST':
        try:
            curr_course = Course.objects.get(course_id=course_id)
            curr_assign = curr_course.authored_assignments.get(assign_id=assign_id)
        except Course.DoesNotExist or Assignment.DoesNotExist:
            raise Http404

        if request.user not in curr_course.instructors.all():
            return Response({'message': 'You are not allowed for this operation.'}, status=status.HTTP_403_FORBIDDEN)
        
        if not curr_assign.current_status == 'published':
            return Response({'message': 'This operation is only allowed for published assignments.'}, status=status.HTTP_403_FORBIDDEN)

        
        if curr_assign.publish_date <= timezone.now() < curr_assign.submission_deadline:
            curr_assign.current_status = 'published'
            curr_assign.published_for_subs = False
            curr_assign.save()
            print(curr_assign.status)
            return Response({'message': 'Assignment published successfully.'}, status=status.HTTP_200_OK)
        return Response({'message': 'Current date is not in range [publish_date, submission_deadline), wait or update the deadline/publish_date.'}, status=status.HTTP_403_FORBIDDEN)
        
        return Response({'message': 'You cannot close the assignment since it was closed already.'}, status=status.HTTP_403_FORBIDDEN)

@api_view(['POST'])
def assignment_publish(request, course_id, assign_id):
    if request.method == 'POST':
        try:
            curr_course = Course.objects.get(course_id=course_id)
            curr_assign = curr_course.authored_assignments.get(assign_id=assign_id)
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

@api_view(['GET', 'POST'])
def assignment_outline_detail(request, course_id, assign_id):
    if request.method == 'GET':
        try:
            curr_course = Course.objects.get(course_id=course_id)
            curr_assign = curr_course.authored_assignments.get(assign_id=assign_id)
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
            curr_assign = curr_course.authored_assignments.get(assign_id=assign_id)
        except Course.DoesNotExist or Assignment.DoesNotExist:
            raise Http404

        if request.user not in curr_course.instructors.all():
            return Response({'message': 'You are not allowed for this operation'}, status=status.HTTP_403_FORBIDDEN)

        if not curr_assign.graded:
            for question in curr_assign.questions.all():
                question.delete()

            post_data = []
            for question in request.data:
                serializer = QuestionSerializer(data=question)
                if serializer.is_valid():
                    serializer.save(parent_assign=curr_assign)
                    post_data.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if len(post_data) > 0:
                print('changing the assign status now from: ', curr_assign.current_status)
                curr_assign.current_status = 'outline_set'
                curr_assign.save()

            return Response(post_data, status=status.HTTP_201_CREATED)
        else:
            return Response({'Message':'The assignment has been graded, only get requests to the page are allowed'}, status=status.HTTP_200_OK)

class CourseCreateView(generics.CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsGlobalInstructor]

    def perform_create(self, serializer):
        serializer.save(
            instructors = [self.request.user],
            entry_key = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(7)])
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
                    body = "You are added to " + course.course_number + " by the course instructor as " + string_role[role] + ". Do not reply to this email."
                    send_mail(subject=sub, message=body, from_email='SwaGrader', recipient_list=[email], fail_silently=False)
                
                return Response({'message': 'succesfully added to the course'}, status=200)

            except SwagraderUser.DoesNotExist:
                # create new user and handle the addition to the course here
                # return Response here as it is
                from django.utils.crypto import get_random_string

                name_split = name.split()
                fname = name_split[0]
                if len(name_split) >= 2: lname = name_split[1]
                else: lname = ""

                pwd = get_random_string(length=10, allowed_chars='abcdefghjkmnpqrstuvwxyz'
                                                                    'ABCDEFGHJKLMNPQRSTUVWXYZ'
                                                                    '23456789')
                user = SwagraderUser(email=email, institute_id=roll_no, first_name=fname, last_name=lname)
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
                body = "You are added to " + course.course_number + " by the course instructor as " + string_role[role] + ". Your account credentials are your email and password: " + pwd + ". This is a system generated email, please do not reply."
                send_mail(subject=sub, message=body, from_email='SwaGrader', recipient_list=[email], fail_silently=False)

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
        course = get_object_or_404(Course, course_id = self.kwargs['course_id'])
        return course.authored_assignments.all()

class AssignmentDetailUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssignmentListCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorForMetadata]
    lookup_field = 'assign_id'

    def get_queryset(self):
        course = get_object_or_404(Course, course_id = self.kwargs['course_id'])
        return course.authored_assignments.all()

    def perform_update(self, serializer):
        from datetime import datetime
        publish_date = serializer.initial_data.get('publish_date')
        submission_deadline = serializer.initial_data.get('submission_deadline')
        format = "%Y-%m-%dT%H:%M"

        published_for_subs = False
        # if datetime.strptime(publish_date, format) <= datetime.now() and datetime.now() < datetime.strptime(submission_deadline, format):
        #     published_for_subs = True

        curr_course = Course.objects.get(course_id=self.kwargs['course_id'])
        serializer.save(course=curr_course, published_for_subs=published_for_subs)

class AssignmentCreateView(generics.CreateAPIView, generics.UpdateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentListCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorForMetadata]
    lookup_field = 'course_id'

    def perform_create(self, serializer):
        from datetime import datetime
        publish_date = serializer.initial_data.get('publish_date')
        submission_deadline = serializer.initial_data.get('submission_deadline')
        format = "%Y-%m-%dT%H:%M"

        published_for_subs = False
        # if datetime.strptime(publish_date, format) <= datetime.now() and datetime.now() < datetime.strptime(submission_deadline, format):
        #     published_for_subs = True
            
        curr_course = Course.objects.get(course_id=self.kwargs['course_id'])
        serializer.save(course=curr_course, published_for_subs=published_for_subs)


    