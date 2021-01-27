from rest_framework import serializers
from authentication.models import EmailNamespace, SwagraderUser
from .models import *
from drf_writable_nested import WritableNestedModelSerializer
from itertools import chain

class EntryKeySerializer(serializers.Serializer):
    entry_key = serializers.CharField(max_length=7, required=True)
    def validate_entry_key(self, value):
        if len(value) == 7: return value
        else: raise ValidationError('Ensure this has exactly 7 chars')

class AssignmentListCreateSerializer(serializers.ModelSerializer):
    course = serializers.StringRelatedField(allow_null=False)
    publish_date = serializers.DateTimeField(required=True)
    submission_deadline = serializers.DateTimeField(required=True)
    late_sub_deadline = serializers.DateTimeField(allow_null=True, required=False)
    allow_late_subs = serializers.BooleanField(default=False)
    published_for_subs = serializers.BooleanField(read_only=True)
    status = serializers.SerializerMethodField()
    graded = serializers.BooleanField(read_only=True)
    grading_methodology = serializers.ReadOnlyField()

    class Meta:
        model = Assignment
        fields = ['assign_id', 'course', 'title', 'pdf', 'publish_date', 'submission_deadline', 'allow_late_subs', 'late_sub_deadline', 'published_for_subs', 'status', 'grading_methodology', 'graded']
    
    def get_status(self, assignment):
        return assignment.current_status

    def validate(self, data):
        sub_deadline = data.get('submission_deadline', -1)
        pub_date = data.get('publish_date', -1)
        late_subs = data.get('allow_late_subs', -1)
        late_sub_deadline = data.get('late_sub_deadline', -1)

        if sub_deadline == -1 and pub_date == -1 and late_subs == -1 and late_sub_deadline == -1:
            return data
            
        if data['submission_deadline'] <= data['publish_date']:
            raise serializers.ValidationError("Submission deadline should not be earlier than publishing date.")

        if data['allow_late_subs']:
            if data['late_sub_deadline'] != None:
                if data['late_sub_deadline'] <= data['submission_deadline']:
                    raise serializers.ValidationError("Late submission deadline should not be earlier than the submission date.")
                return data
            raise serializers.ValidationError("Set the late submission deadline for the assignment or uncheck the allow late sub flag.")
        return data

class CourseDetailInstructorSerializer(serializers.ModelSerializer):
    instructors = serializers.StringRelatedField(many=True, allow_null=False)
    authored_assignments = AssignmentListCreateSerializer(many=True, read_only=True)
    ta_count = serializers.SerializerMethodField()
    st_count = serializers.SerializerMethodField()
    course_avg = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['instructors', 'course_id', 'course_number', 'course_title', 'entry_key','term', 'year', 'entry_restricted', 'st_count', 'ta_count', 'course_avg', 'authored_assignments']

    def get_assignments(self, course):
        assigns = course.authored_assignments.filter(published_for_subs=True)
        graded_assigns = course.authored_assignments.filter(graded=True)
        chained = chain(assigns, graded_assigns)
        ser = AssignmentListCreateSerializer(assigns, many=True)
        return ser.data

    def get_ta_count(self, course):
        return course.teaching_assistants.all().count()
    
    def get_st_count(self, course):
        return course.students.all().count()
    
    def get_course_avg(self, course):
        graded_assign = course.authored_assignments.filter(graded=True)
        if graded_assign.count() != 0:
            tot = 0
            for assign in graded_assign:
                tot += assign.average
            return tot/graded_assign.count()
        return "Course has no assignment graded till now."

class CourseSerializer(serializers.ModelSerializer):
    instructors = serializers.StringRelatedField(many=True)
    roles = serializers.SerializerMethodField()
    authored_assignments = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ['instructors', 'course_id', 'course_number', 'course_title', 'term', 'year', 'entry_restricted', 'roles', 'authored_assignments']
    
    def get_authored_assignments(self, course):
        assigns = course.authored_assignments.filter(published_for_subs=True)
        graded_assigns = course.authored_assignments.filter(graded=True)
        chained = chain(assigns, graded_assigns)
        ser = AssignmentListCreateSerializer(assigns, many=True)
        return ser.data

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

    def validate_email(self, value):
        domain = value[value.rfind('@')+1 :]
        if EmailNamespace.objects.filter(namespace=domain).exists():
            return value
        else:
            raise ValidationError('The user should have the institute defined domain namespace.')

class CourseMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMetadata
        fields = ['description', 'grading_policy', 'peergrading_policy', 'regrading_policy']

class CourseRosterSerializer(serializers.ModelSerializer):
    # course = serializers.StringRelatedField()
    user = serializers.StringRelatedField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = Roster
        fields = ['id', 'user', 'role']

    def get_role(self, roster):
        role = []
        if roster.user in roster.course.instructors.all():  role.append('instructor')
        if roster.user in roster.course.teaching_assistants.all(): role.append('ta')
        if roster.user in roster.course.students.all(): role.append('student') 
        return role
    

class GlobalRubricSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalRubric
        fields = ['description', 'marks'] 

class GlobalSubrubricSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalSubrubric
        fields = ['description', 'marks']

    
class SubQuestionSerializer(WritableNestedModelSerializer):
    parent_ques = serializers.StringRelatedField(allow_null=False)
    global_subrubrics = serializers.SerializerMethodField()

    class Meta:
        model = SubQuestion
        fields = ['parent_ques','sno', 'sques_id', 'title', 'min_marks', 'max_marks', 'global_subrubrics']
    
    def get_global_subrubrics(self, sques):
        subrubrics = sques.g_subrubrics.all()
        ser = GlobalSubrubricSerializer(subrubrics, many=True)
        return ser.data

class QuestionSerializer(WritableNestedModelSerializer):
    parent_assign = serializers.StringRelatedField(allow_null=False)
    sub_questions = SubQuestionSerializer(many=True, allow_null=True)
    global_rubrics = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['parent_assign', 'sno', 'ques_id', 'title', 'min_marks', 'max_marks', 'global_rubrics', 'sub_questions']

    def get_global_rubrics(self, ques):
        rubrics = ques.g_rubrics.all()
        ser = GlobalRubricSerializer(rubrics, many=True)
        return ser.data

class QuestionListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Question
        fields = ['ques_id', 'sno', 'title', 'min_marks', 'max_marks']

class StagingRosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SwagraderUser
        fields = ['email', 'first_name', 'last_name', 'institute_id']
    
