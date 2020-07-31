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
import random, string
from datetime import datetime
from django.utils.timezone import timezone

class EnrollCourseView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EntryKeySerializer
    def post(self, request, format=None):
        ser = EntryKeySerializer(data=request.data)
        if ser.is_valid(raise_exception=True):
            course = get_object_or_404(Course, entry_key=ser.data.get('entry_key'))
            if course.entry_restricted:
                return Response({'message': 'Entry in this course is restricted'}, status=403)
            else:
                course.students.add(request.user)
                return Response({'message': 'Successfully added to the course.', 'course_id': course.course_id}, status=200)