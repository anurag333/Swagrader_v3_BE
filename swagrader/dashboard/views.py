from django.shortcuts import render
from rest_framework import generics, views, permissions, mixins
from rest_framework.response import Response
from authentication.models import EmailNamespace
from .serializers import *
from .permissions import *
from .models import *
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
        
        privileges = ['student']
        if request.user.global_instructor_privilege:
            privileges.append('instructor')
        else: 
            request.user.global_ta_privilege
            privileges.append('ta')

        data = {'privileges': privileges}
        data['courses'] = []
        for course in min_list.data:
            data['courses'].append(course)

        return Response(data)

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

class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructor]
    lookup_field = 'course_id'

class AssignmentCreateView(generics.CreateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorForMetadata]
    lookup_field = 'course_id'

    def perform_create(self, serializer):
        curr_course = Course.objects.get(course_id=self.kwargs['course_id'])
        serializer.save(course=curr_course)
        
# class UpdateRosterCsv(generics.UpdateAPIView):
#     permission_classes = [permissions.IsAuthenticated, IsInstructor]
#     serializer_class = RosterCsvSerializer
#     queryset = Course.objects.all()

    
#     def perform_update(self, serializer):
#         course = serializer.save()
#         roster_path = bulkpath = course.roster_file.path
#         print(roster_path)
#         data = pd.read_excel(roster_path)
#         if len(data.columns) == 5:
#             for col in data.columns:
#                 if col not in ['ID', 'firstname', 'lastname', 'email', 'role']:
#                     raise APIException(detail="column names should be as per the template, update the roster file")
#         else:
#             raise APIException(detail="insufficient number of columns, update the roster file")

#         for obj in data.itertuples():
#             id = obj.ID
#             firstname = obj.firstname
#             lastname = obj.lastname
#             email = obj.email
#             role = obj.role
            
#             # check if user with that email already exists, if yes, then add him in the course
#             user = User.objects.filter(email=email)
#             print(user)
#             if user.count() != 0:
#                 user = user.first()
#                 if user.acad_profile.vf_number is None:
#                     user.acad_profile.vf_number = id
#                 if role == "st" and user not in course.students.all():
#                     course.students.add(user)
#                     # email_existing_user(course, role, email)

#                 elif role == "ta" and user not in course.teaching_assistants.all():
#                     course.teaching_assistants.add(user)
#                     Mapper.objects.create(ta_role=user, course=course)
#                     ProbeGrader.objects.create(ta_role=user, course=course)
#                     email_existing_user(course, role, email)

#                 elif role == "in" and user not in course.instructors.all():
#                     course.instructors.add(user)
#                     email_existing_user(course, role, email)
#                 else:
#                     continue
#             else:
#                 # create a user
#                 username = firstname+str(id)+''.join(random.choice(string.ascii_letters)for n in range(3))
#                 password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
#                 user = User.objects.create_user(username, email, password)
#                 user.last_name = lastname
#                 user.first_name = firstname
#                 user.save()
#                 user.acad_profile.vf_number = id
#                 user.acad_profile.save()
#                 if role == "st":
#                     course.students.add(user)
#                     Peer.objects.create(st_role=user.acad_profile, course=course)
#                     # email_new_user(course, role, username, password, email)
#                 elif role == "ta":
#                     course.teaching_assistants.add(user)
#                     Mapper.objects.create(ta_role=user, course=course)
#                     ProbeGrader.objects.create(ta_role=user, course=course)
#                     email_new_user(course, role, username, password, email)
#                 elif role == "in":
#                     course.instructors.add(user)
#                     email_new_user(course, role, username, password, email)
#                 else:
#                     continue
        