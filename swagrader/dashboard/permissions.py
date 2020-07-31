from rest_framework.permissions import BasePermission
from .models import Course
from itertools import chain
class IsGlobalInstructor(BasePermission):
    """
    Permission to allow only instructor to have the view permissions (Course)
    """
    def has_permission(self, request, view):
        return request.user.global_instructor_privilege

class IsAssociatedToTheCourse(BasePermission):
    """
    Permission to allow only TA to have the obj permissions (Course)
    """ 
    def has_object_permission(self, request, view, obj):
        return request.user in chain(obj.instructors.all(), obj.teaching_assistants.all(), obj.students.all())

class IsGlobalTA(BasePermission):
    """
    Permission to allow only TA to have the obj permissions (Course)
    """
    def has_permission(self, request, view):
        return request.user.global_ta_privilege

class IsInstructor(BasePermission):
    """
    Permission to allow only instructor to have the obj permissions (Course)
    """
    def has_object_permission(self, request, view, obj):
        print(obj, " is the obj")
        return request.user in obj.instructors.all()
    
    def has_permission(self, request, view):
        # print(request.META, " meta for the req")
        course_id = view.kwargs.get('course_id', None)
        if course_id:
            course = Course.objects.filter(course_id=course_id)
            if len(course):
                course = course.first()
                return request.user in course.instructors.all()

        else:
            return False

class IsInstructorForMetadata(BasePermission):
    """
    Permission to allow only instructor to have the obj permissions (Course)
    """
    def has_object_permission(self, request, view, obj):
        print(obj, " is the obj")
        return request.user in obj.course.instructors.all()
    
    def has_permission(self, request, view):
        # print(request.META, " meta for the req")
        course_id = view.kwargs.get('course_id', None)
        if course_id:
            course = Course.objects.filter(course_id=course_id)
            if len(course):
                course = course.first()
                return request.user in course.instructors.all()

        else:
            return False
        
