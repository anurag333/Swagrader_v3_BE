from functools import total_ordering
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
import uuid


class Course(models.Model):
    """
    Course schema for Swagrader.
    """
    course_id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True)
    instructors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 'instructed_courses')
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='enrolled_courses', blank=True)
    teaching_assistants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='assisted_courses', blank=True)
    course_number = models.CharField(max_length=6)
    course_title = models.CharField(max_length=40)
    term = models.CharField(max_length=6, choices=(
        ('Summer', 'Summer'), ('Winter', 'Winter'), ('Spring', 'Spring'), ('Fall', 'Fall')))
    year = models.IntegerField()
    created = models.DateField(auto_now_add=True)
    entry_key = models.CharField(editable=False, max_length=7)
    entry_restricted = models.BooleanField(default=False)

    def __str__(self):
        return '{0}: {1}'.format(self.course_number, self.course_title)

    class Meta:
        ordering = ['-created', ]


class CourseMetadata(models.Model):
    course = models.OneToOneField(
        Course, on_delete=models.CASCADE, related_name='course_metadata')
    description = models.TextField(blank=True, null=True)
    grading_policy = models.TextField(blank=True, null=True)
    peergrading_policy = models.TextField(blank=True, null=True)
    regrading_policy = models.TextField(blank=True, null=True)

    def __str__(self):
        return '{0}: Metadata'.format(self.course)


class Roster(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='roster_detail')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)


class Assignment(models.Model):

    def assignment_path(self, filename):
        # file will be uploaded to MEDIA_ROOT/course_<course_number>/<assignment_title>/Question_paper/<filename>
        title = self.title.replace(' ', '_')
        return 'course_{0}-{3}/{1}/Question_paper/{2}'.format(self.course.course_number, title, filename, str(self.course.course_id)[0:6])

    def answer_path(self, filename):
        # file will be uploaded to MEDIA_ROOT/course_<course_number>/<assignment_title>/Answer_Key/<filename>
        title = ""
        for c in self.title:
            if c == " ":
                title += "_"
            else:
                title += c

        return 'course_{0}-{3}/{1}/Answer_Key/{2}'.format(self.course.course_number, title, filename, str(self.course.course_id)[0:6])

    assign_id = models.BigAutoField(primary_key=True)
    pdf = models.FileField(upload_to=assignment_path, validators=[
                           FileExtensionValidator(allowed_extensions=['pdf', 'txt'])])
    answer_pdf = models.FileField(upload_to=answer_path, validators=[FileExtensionValidator(
        allowed_extensions=['pdf', 'doc', 'txt'])], null=True, blank=True)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='authored_assignments')
    title = models.CharField(max_length=30)
    date_created = models.DateField(auto_now_add=True)
    publish_date = models.DateTimeField()
    submission_deadline = models.DateTimeField()
    allow_late_subs = models.BooleanField()
    late_sub_deadline = models.DateTimeField(null=True)
    late_sub_penalty = models.FloatField(default=0)
    weightage = models.FloatField(default=0)
    published_for_subs = models.BooleanField(default=False)
    average = models.FloatField(default=0)
    regrading_requests = models.BooleanField(default=True)
    grading_methodology = models.CharField(max_length=2, choices=(
        ('pg', 'Peergrading'), ('ng', 'Normal grading')), default='pg')
    graded = models.BooleanField(default=False)
    current_status = models.CharField(max_length=20, choices=(
        ('set_outline', 'Set outline'),
        ('outline_set', 'publish assign'),
        ('published', 'close submissions'),
        ('subs_closed', 'Select grading method'),
        ('method_selected', 'Stage for grading'),
        ('grading_started', 'Grading Started'),
        ('rubric_set', 'start probe grading'),
        ('papers_distributed', 'start peergrading'),
        ('grading_ended', 'assignment finished')
    ), default='set_outline')

    def __str__(self):
        return '{0}: {1}'.format(self.course.course_number, self.title)


class AssignmentGradingProfile(models.Model):
    assignment = models.OneToOneField(
        Assignment, on_delete=models.CASCADE, related_name="assignment_grading_profile")
    mapping_deadline = models.DateField(null=True, blank=True)
    grading_deadline = models.DateField(null=True, blank=True)
    regrading_deadline = models.DateField(null=True, blank=True)
    current_status = models.CharField(max_length=15, choices=(
        ('set rubric', 'Set global rubrics'),
        ('stage', 'Stage grading'),
        ('start', 'Start grading'),
        ('end', 'End grading')), default='outline')
    instructor_graders = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 'in_graded_assignments')
    ta_graders = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='ta_graded_assignments', blank=True)


class AssignmentPeergradingProfile(models.Model):
    # alpha
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="assignment_peergrading_profile")
    param_mu = models.FloatField(
        help_text='Parameter to be set as per the TRUPEQA algorithm', default=16.234)
    param_gm = models.FloatField(
        help_text='Parameter to be set as per the TRUPEQA algorithm', default=1.234)
    peerdist = models.IntegerField(
        default=6, help_text='This is the number of copies that will be distributed to peers.')
    probing_deadline = models.DateTimeField(null=True, blank=True)
    peergrading_deadline = models.DateTimeField(null=True, blank=True)
    n_probes = models.IntegerField(
        default=20, help_text='These are the number of probes you want to set for this assignment.')

    instructor_graders = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 'in_pgraded_assignments')
    peergraders = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='st_pgraded_assignments', blank=True)
    ta_graders = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='ta_pgraded_assignments', blank=True)


"""
Each assignment will comprise of some questions, which are instantiations of the question model class.
"""


class Question(models.Model):
    ques_id = models.BigAutoField(primary_key=True)
    parent_assign = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name='questions')
    sno = models.IntegerField(default=0)
    title = models.CharField(max_length=200)
    min_marks = models.FloatField(default=0)
    max_marks = models.FloatField(default=0)

    def __str__(self):
        return '{0}: Ques_{1}'.format(self.parent_assign.title, self.sno)

    class Meta:
        ordering = ['sno']


"""
Each question will comprise of some sub-questions, which are instantiations of the sub-question model class.
"""


class SubQuestion(models.Model):
    sques_id = models.BigAutoField(primary_key=True)
    parent_ques = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='sub_questions')
    sno = models.IntegerField(default=0)
    title = models.CharField(max_length=200)
    min_marks = models.FloatField(default=0)
    max_marks = models.FloatField(default=0)

    def __str__(self):
        return 'Ques_{0}: SubQues_{1}'.format(self.parent_ques.sno, self.sno)

    class Meta:
        ordering = ['sno']


class AssignmentSubmission(models.Model):
    sub_id = models.BigAutoField(primary_key=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name='assign_submissions')

    def __str__(self):
        return f'{self.sub_id}-{self.assignment.title}: {self.author.institute_id} Submission'


class QuestionSubmission(models.Model):
    def qsub_path(self, filename):
        # file will be uploaded to MEDIA_ROOT/course_<course_number>/<assignment_title>/Submissions/<question_sno>/<filename>
        assign = self.submission.assignment
        title = assign.title.replace(' ', '_')
        return 'course_{0}-{3}/{1}/Submissions/{4}/{2}'.format(assign.course.course_number, title, filename, str(assign.course.course_id)[0:6], str(self.question.sno))

    qsub_id = models.BigAutoField(primary_key=True)
    submission = models.ForeignKey(
        AssignmentSubmission, on_delete=models.CASCADE, related_name='submissions')
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='qsubmissions')
    pdf = models.FileField(upload_to=qsub_path, validators=[
                           FileExtensionValidator(allowed_extensions=['pdf'])])


class GlobalRubric(models.Model):
    rubric_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='g_rubrics')
    description = models.CharField(max_length=100)
    marks = models.IntegerField(default=0)


class GlobalSubrubric(models.Model):
    sub_rubric_id = models.AutoField(primary_key=True)
    sub_question = models.ForeignKey(
        SubQuestion, on_delete=models.CASCADE, related_name='g_subrubrics')
    description = models.CharField(max_length=100)
    marks = models.IntegerField(default=0)


class ProbeSubmission(models.Model):
    probe_id = models.BigAutoField(primary_key=True)
    parent_sub = models.ForeignKey(
        AssignmentSubmission, on_delete=models.CASCADE, related_name='probe_submission')
    probe_grader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='probes_to_check', blank=True, null=True)
    true_score = models.FloatField(default=0)


class ProbeSubmissionQuestion(models.Model):
    probe_ques_id = models.AutoField(primary_key=True)
    parent_probe_sub = models.ForeignKey(
        ProbeSubmission, on_delete=models.CASCADE, related_name='probe_questions')
    parent_ques = models.OneToOneField(
        QuestionSubmission, on_delete=models.CASCADE, related_name='probe_counterpart')
    rubric = models.ForeignKey(
        GlobalRubric, on_delete=models.CASCADE, related_name='global_rubric', null=True, blank=True)
    # true_score = models.FloatField(default=0)


class ProbeSubmissionQuestionComment(models.Model):
    probe_ques_com_id = models.AutoField(primary_key=True)
    parent_ques = models.OneToOneField(
        ProbeSubmissionQuestion, on_delete=models.CASCADE, related_name='comment')
    comment = models.TextField()
    marks = models.FloatField(default=0)


class ProbeSubmissionSubquestion(models.Model):
    probe_subques_id = models.AutoField(primary_key=True)
    parent_probe_ques = models.ForeignKey(
        ProbeSubmissionQuestion, on_delete=models.CASCADE, related_name='probe_subquestions')
    sub_rubric = models.ForeignKey(
        GlobalSubrubric, on_delete=models.CASCADE, related_name='global_sub_rubric',  null=True, blank=True)
    parent_sub_ques = models.ForeignKey(
        SubQuestion, on_delete=models.CASCADE, null=True, blank=True)
    # true_score = models.FloatField(default=0)


class ProbeSubmissionSubquestionComment(models.Model):
    probe_subques_com_id = models.AutoField(primary_key=True)
    parent_subques = models.OneToOneField(
        ProbeSubmissionSubquestion, on_delete=models.CASCADE, related_name='sub_comment')
    sub_comment = models.TextField
    marks = models.FloatField(default=0)


class ProbeRubric(models.Model):
    probe_rub_id = models.AutoField(primary_key=True)
    rubric = models.OneToOneField(
        GlobalRubric, on_delete=models.CASCADE, related_name='probe_rubric')
    selected = models.BooleanField(default=False)


class ProbeSubrubric(models.Model):
    probe_subrub_id = models.AutoField(primary_key=True)
    sub_rubric = models.OneToOneField(
        GlobalSubrubric, on_delete=models.CASCADE, related_name='probe_subrubric')
    selected = models.BooleanField(default=False)

########################################################################


class PeerGraders(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='papers_to_check')
    paper = models.ForeignKey(
        AssignmentSubmission, on_delete=models.CASCADE, related_name='checked_by')

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['student', 'paper'], name='student-paper')]


class PeerSubmissionQuestion(models.Model):
    peer_ques_id = models.AutoField(primary_key=True)
    parent_ques = models.ForeignKey(
        QuestionSubmission, on_delete=models.CASCADE, related_name='peer_counterpart')
    rubric = models.ForeignKey(
        GlobalRubric, on_delete=models.CASCADE, related_name='peer_rubric', default=None, null=True, blank=True)
    parent_tuple = models.ForeignKey(
        PeerGraders, on_delete=models.CASCADE, related_name='question_submissions')


class PeerSubmissionSubquestion(models.Model):
    peer_subques_id = models.AutoField(primary_key=True)
    parent_peer_ques = models.ForeignKey(
        PeerSubmissionQuestion, on_delete=models.CASCADE, related_name='peer_subquestions')
    sub_rubric = models.ForeignKey(
        GlobalSubrubric, on_delete=models.CASCADE, related_name='peer_sub_rubric', default=None, null=True, blank=True)
    parent_sub_ques = models.ForeignKey(
        SubQuestion, on_delete=models.CASCADE, null=True, blank=True)

class Marks(models.Model):
    m_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='get_marks')
    ques = models.ForeignKey(Question, on_delete=models.CASCADE)
    marks = models.FloatField(default=0)
    bonus = models.FloatField(default=0)
    total_marks = models.FloatField(default=0)


class BiasReliability(models.Model):
    br_id = models.AutoField(primary_key=True)
    ques = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    bi = models.FloatField(default=0)
    ti = models.FloatField(default=0)
