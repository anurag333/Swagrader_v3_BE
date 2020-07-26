from django.shortcuts import render
from rest_framework import generics, views, permissions
from rest_framework.response import Response
from authentication.models import EmailNamespace
from .serializers import *
from .permissions import *
from .models import Course
from itertools import chain
import random
import string 

class EmailNamespaceListView(generics.ListAPIView):
    queryset = EmailNamespace.objects.all()
    serializer_class = EmailNamespaceSerializer
    permission_classes = [permissions.AllowAny]

class CourseListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    # authentication_classes = [authentication.TokenAuthentication]

    def get(self, request, format = None):
        inst_courses = request.user.instructed_courses.all()
        stu_courses = request.user.enrolled_courses.all()
        ta_courses = request.user.assisted_courses.all()

        buffer_courses = list(chain(inst_courses, stu_courses, ta_courses))

        min_list = CourseSerializer(buffer_courses, many=True, context={'current_user': request.user})  
        return Response(min_list.data)

class CourseCreateView(generics.CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsGlobalInstructor]

    def perform_create(self, serializer):
        serializer.save(
            instructors = [self.request.user],
            entry_key = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(7)])
        )


class AddSingleUserView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]
    serializer_class = SingleUserSerializer
    queryset = Course.objects.all()
    

    def post(self, request, course_uid, format=None):
        try:
            course = Course.objects.get(course_id=course_uid)
        except Course.DoesNotExist:
            return Response({'message': 'The course does not exist'}, status=404)
        
        ser = SingleUserSerializer(data=request.data)
        print(ser.initial_data)
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
                if role == 's':
                    course.students.add(user)
                elif role == 't':
                    course.teaching_assistants.add(user)
                elif role == 'i':
                    course.instructors.add(user)
                else: 
                    return Response({'message': 'Malformed role input'}, status=400)
                course.save()

                if notify:
                    from django.core.mail import send_mail
                    sub = "Added to " + course.course_number
                    body = "You are added to " + course.course_number + " by the course instructor as " + string_role[role] + ". Do not reply to this email."
                    send_mail(subject=sub, message=body, from_email='SwaGrader', recipient_list=[email], fail_silently=False)
                
                return Response({'message': 'succesfully added to the course'}, status=200)

            except SwagraderUser.DoesNotExist:
                # create new user and handle the addition to the course here
                # return Response here as it is
                print("Creating new user ...")
                from django.utils.crypto import get_random_string

                name_split = name.split()
                fname, lname = name_split[0], name_split[1]
                pwd = get_random_string(length=10, allowed_chars='abcdefghjkmnpqrstuvwxyz'
                                                                    'ABCDEFGHJKLMNPQRSTUVWXYZ'
                                                                    '23456789')
                user = SwagraderUser(email=email, institute_id=roll_no, first_name=fname, last_name=lname)
                user.set_password(pwd)

                print(user, " this will be created, with role: ", string_role[role])

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

                if notify:
                    from django.core.mail import send_mail
                    sub = "Added to " + course.course_number 
                    body = "You are added to " + course.course_number + " by the course instructor as " + string_role[role] + ". Your account credentials are your email and password: " + pwd + ". This is a system generated email, please do not reply."
                    send_mail(subject=sub, message=body, from_email='SwaGrader', recipient_list=[email], fail_silently=False)

                return Response({'message': 'succesfully added to the course'}, status=200)


        return Response({'message': ser.errors}, status=400)
        
