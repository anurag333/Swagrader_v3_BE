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


class EmailNamespaceListView(generics.ListAPIView):
    queryset = EmailNamespace.objects.all()
    serializer_class = EmailNamespaceSerializer
    permission_classes = [permissions.AllowAny]


class CourseListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    # authentication_classes = [authentication.TokenAuthentication]

    def get(self, request, format=None):
        inst_courses = request.user.instructed_courses.all()
        stu_courses = request.user.enrolled_courses.all()
        ta_courses = request.user.assisted_courses.all()

        buffer_courses = set(chain(inst_courses, stu_courses, ta_courses))

        min_list = CourseSerializer(buffer_courses, many=True, context={
                                    'current_user': request.user})

        privileges = ['student']
        if request.user.global_instructor_privilege:
            privileges.append('instructor')
        if request.user.global_ta_privilege:
            privileges.append('ta')

        data = {'privileges': privileges}
        data['courses'] = []
        for course in min_list.data:
            data['courses'].append(course)

        return Response(data)
