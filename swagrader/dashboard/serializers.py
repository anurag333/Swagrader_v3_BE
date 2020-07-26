from rest_framework import serializers
from authentication.models import EmailNamespace, SwagraderUser
from .models import Course

class EmailNamespaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailNamespace
        fields = ['namespace']


class CourseSerializer(serializers.ModelSerializer):
    instructors = serializers.StringRelatedField(many=True)
    roles = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ['instructors', 'course_id', 'course_number', 'course_title', 'term', 'year', 'entry_restricted', 'roles']

    def get_roles(self, course):
        current_user = self.context.get('current_user')
        roles = []
        if current_user in course.instructors.all():
            roles.append('instructor')
        if current_user in course.students.all():
            roles.append('student')
        if current_user in course.teaching_assistants.all():
            roles.append('ta')
        return roles

class SingleUserSerializer(serializers.Serializer):
    name = serializers.CharField(max_length = 30, required=True)
    email = serializers.EmailField(required=True)
    institute_id = serializers.IntegerField(required=True)
    role = serializers.ChoiceField(choices=(('s', 'Student'), ('t', 'Teaching Assistant'), ('i', 'Instructor')), allow_blank=False)
    notify = serializers.BooleanField(default=True)
    
# class AssignmentSerializer(serializers.ModelSerializer):
#     course = serializers.StringRelatedField(allow_null=False)
#     status = serializers.SerializerMethodField(read_only=True)
#     under_config = serializers.IntegerField(read_only=True)
#     under_mapping = serializers.IntegerField(read_only=True)
#     under_grading = serializers.IntegerField(read_only=True)
#     under_regrading = serializers.IntegerField(read_only=True)
#     graded = serializers.IntegerField(read_only=True)


#     class Meta:
#         model = Assignment
#         fields = ['id', 'course', 'title', 'date_posted', 'regrading_requests', 'status', 'pdf', 'answer_pdf', 'peergrading', 'param_mu', 'param_gm', 'under_config', 'under_mapping', 'under_grading', 'under_regrading', 'graded']
    
#     def get_status(self, assign):
#         if assign.under_mapping == 1:
#             return "Under mapping"
#         elif assign.under_config == 1:
#             return "Outline to be set"
#         elif assign.under_grading == 1:
#             return "Under grading"
#         elif assign.under_regrading == 1:
#             return "Under regrading"
#         elif assign.graded == 1:
#             return "Graded"
    
#     def validate_title(self, value):
#         if ' ' in value.lower():
#             raise serializers.ValidationError("There should be no spaces in the title of the Assignment")
#         return value

# class CourseDetailSerializer(serializers.ModelSerializer):
#     instructors = serializers.StringRelatedField(many=True, allow_null=False)
#     authored_assignments = AssignmentSerializer(many=True, read_only=True)
#     ta_count = serializers.SerializerMethodField()
#     st_count = serializers.SerializerMethodField()
#     course_avg = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Course
#         fields = ['instructors', 'course_id', 'course_number', 'course_title', 'course_description', 'term', 'year', 'entry_restricted', 'st_count', 'ta_count', 'course_avg', 'authored_assignments']

#     def get_ta_count(self, course):
#         return course.teaching_assistants.all().count()
    
#     def get_st_count(self, course):
#         return course.students.all().count()
    
#     def get_course_avg(self, course):
#         graded_assign = course.authored_assignments.filter(graded=1)
#         if graded_assign.count() != 0:
#             tot = 0
#             for assign in graded_assign:
#                 tot += assign.average
#             return tot/graded_assign.count()
#         return "Course has no assignment graded till now."
