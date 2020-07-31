from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
import uuid

class Course(models.Model):
    """
    Course schema for Swagrader.
    """
    course_id               = models.UUIDField(default = uuid.uuid4, editable = False, primary_key = True)
    instructors             = models.ManyToManyField(settings.AUTH_USER_MODEL, 'instructed_courses')
    students                = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_courses', blank=True)
    teaching_assistants     = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name = 'assisted_courses', blank=True)
    course_number           = models.CharField(max_length = 6)
    course_title            = models.CharField(max_length = 40)
    term                    = models.CharField(max_length = 6, choices = (('Summer','Summer'),('Winter','Winter'),('Spring','Spring'),('Fall','Fall')))
    year                    = models.IntegerField()
    created                 = models.DateField(auto_now_add=True)
    entry_key               = models.CharField(editable = False, max_length = 7)
    entry_restricted        = models.BooleanField(default = False)

    def __str__(self):
        return '{0}: {1}'.format(self.course_number, self.course_title)
    
    class Meta:
        ordering = ['-created',]

class CourseMetadata(models.Model):
    course              = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='course_metadata')
    description         = models.TextField(blank=True, null=True)
    grading_policy      = models.TextField(blank=True, null=True)
    peergrading_policy  = models.TextField(blank=True, null=True)
    regrading_policy    = models.TextField(blank=True, null=True)

    def __str__(self):
        return '{0}: Metadata'.format(self.course)

class Roster(models.Model):
    course         = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='roster_detail')
    user           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Assignment(models.Model):
    
    def assignment_path(instance, filename):
        # file will be uploaded to MEDIA_ROOT/course_<course_number>/<assignment_title>/Question_paper/<filename>
        title = ""
        for c in instance.title:
            if c == " ":
                title += "_"
            else:
                title += c
        return 'course_{0}-{3}/{1}/Question_paper/{2}'.format(instance.course.course_number, title, filename, str(instance.course.course_id)[0:6])
    
    def answer_path(instance, filename):
        # file will be uploaded to MEDIA_ROOT/course_<course_number>/<assignment_title>/Answer_Key/<filename>
        title = ""
        for c in instance.title:
            if c == " ":
                title += "_"
            else:
                title += c

        return 'course_{0}-{3}/{1}/Answer_Key/{2}'.format(instance.course.course_number, title, filename, str(instance.course.course_id)[0:6])
    
    assign_id                           = models.BigAutoField(primary_key=True)
    pdf                                 = models.FileField(upload_to = assignment_path, validators=[FileExtensionValidator(allowed_extensions=['pdf'])]) 
    answer_pdf                          = models.FileField(upload_to=answer_path, validators=[FileExtensionValidator(allowed_extensions=['pdf','doc','txt'])], null=True, blank=True)
    course                              = models.ForeignKey(Course, on_delete = models.CASCADE, related_name = 'authored_assignments')
    title                               = models.CharField(max_length = 30)
    date_created                        = models.DateField(auto_now_add = True)
    publish_date                        = models.DateTimeField()
    submission_deadline                 = models.DateTimeField()
    allow_late_subs                     = models.BooleanField()
    late_sub_deadline                   = models.DateTimeField(null=True)
    published_for_subs                  = models.BooleanField(default=False)
    average                             = models.FloatField(default=0)
    regrading_requests                  = models.BooleanField(default = True)
    grading_methodology                 = models.CharField(max_length=2, choices=(('pg', 'Peergrading'), ('ng', 'Normal grading')), default='ng')
    graded                              = models.BooleanField(default=False)
    current_status                      = models.CharField(max_length=20, choices=(
                                            ('set_outline', 'Set outline'),
                                            ('outline_set', 'publish assign'),
                                            ('published', 'close submissions'),
                                            ('close_subs', 'Map submissions'),
                                            ('select method', 'Select grading methodology'),
                                            ), default='set_outline')
                                            
    def __str__(self):
        return '{0}: {1}'.format(self.course.course_number, self.title)
    

class AssignmentGradingProfile(models.Model):
    assignment                          = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name="assignment_grading_profile")
    mapping_deadline                    = models.DateField(null=True, blank=True)
    grading_deadline                    = models.DateField(null=True, blank=True)
    regrading_deadline                  = models.DateField(null=True, blank=True)
    current_status                      = models.CharField(max_length=15, choices=(
                                            ('outline', 'Set outline'),
                                            ('publish', 'Publish assignment'),
                                            ('set rubric', 'Set global rubrics'),
                                            ('select method', 'Select grading methodology'),
                                            ('stage', 'Stage grading'),
                                            ('start', 'Start grading'),
                                            ('end', 'End grading')), default='outline')

class AssignmentPeergradingProfile(models.Model):
    assignment              = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name="assignment_peergrading_profile")
    param_mu                = models.FloatField(help_text='Parameter to be set as per the TRUPEQA algorithm', default=16.234)
    param_gm                = models.FloatField(help_text='Parameter to be set as per the TRUPEQA algorithm', default=1.234)
    peerdist                = models.IntegerField(default=6, help_text='This is the number of copies that will be distributed to peers.')
    probing_deadline        = models.DateField(null=True, blank=True)
    peergrading_deadline    = models.DateField(null=True, blank=True)
    n_probes                = models.IntegerField(default=20, help_text='These are the number of probes you want to set for this assignment.')


"""
Each assignment will comprise of some questions, which are instantiations of the question model class.
"""
class Question(models.Model):
    ques_id         = models.BigAutoField(primary_key=True)
    parent_assign   = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='questions')
    sno             = models.IntegerField(default=0)
    title           = models.CharField(max_length=200)
    marks           = models.FloatField(default=0)

    def __str__(self):
        return '{0}: Ques_{1}'.format(self.parent_assign.title, self.sno)

    class Meta:
        ordering = ['sno']

"""
Each question will comprise of some sub-questions, which are instantiations of the sub-question model class.
"""
class SubQuestion(models.Model):
    sques_id        = models.BigAutoField(primary_key=True)
    parent_ques     = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='sub_questions')
    sno             = models.IntegerField(default=0)
    title           = models.CharField(max_length=200)
    marks           = models.FloatField(default=0)

    def __str__(self):
        return 'Ques_{0}: SubQues_{1}'.format(self.parent_ques.sno, self.sno)

    class Meta:
        ordering = ['sno']
