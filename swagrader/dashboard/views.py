from django.shortcuts import render
from rest_framework import generics, views, permissions
from authentication.models import EmailNamespace
from .serializers import EmailNamespaceSerializer, CourseSerializer
from .models import Course

class EmailNamespaceListView(generics.ListAPIView):
    queryset = EmailNamespace.objects.all()
    serializer_class = EmailNamespaceSerializer
    permission_classes = [permissions.AllowAny]

class CourseListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    # authentication_classes = [authentication.TokenAuthentication]

    def get(self, request, format = None):
        inst_courses = request.user.authored_courses.all()
        stu_courses = request.user.enrolled_courses.all()
        ta_courses = request.user.assisted_courses.all()

        buffer_courses = list(chain(inst_courses, stu_courses, ta_courses))

        min_list = CourseSerializer(buffer_courses, many=True, context={'current_user': request.user})  
        return Response(min_list.data)

class CourseCreateView(generics.CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer()
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(
            instructors = [self.request.user],
            entry_key = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(7)])
        )
