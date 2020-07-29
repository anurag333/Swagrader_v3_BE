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
        return 'course_{0}-{3}/{1}/Question_paper/{2}'.format(instance.course.course_number, instance.title, filename, str(instance.course.course_id)[0:6])
    
    
    def validate_title(value):
        if ' ' in value:
            raise ValidationError(
                _('%(value) should have no spaces.'),
                params={'value': value},
            )

    pdf                 = models.FileField(upload_to = assignment_path, validators=[FileExtensionValidator(allowed_extensions=['pdf','doc','txt'])]) 
    course              = models.ForeignKey(Course, on_delete = models.CASCADE, related_name = 'authored_assignments')
    title               = models.CharField(max_length = 20, help_text="There should be no spaces, Assign_1 is valid, Assign 1 is invalid.", validators=[validate_title])
    date_posted         = models.DateField(auto_now_add = True)
    publish_date        = models.DateTimeField()
    submission_deadline = models.DateTimeField()
    allow_late_subs     = models.BooleanField()
    late_sub_deadline   = models.DateTimeField(null=True)
    average             = models.FloatField(default=0)

    def __str__(self):
        return '{0}: {1}'.format(self.course.course_number, self.title)
    

class AssignmentGradingProfile(models.Model):
    def answer_path(instance, filename):
        # file will be uploaded to MEDIA_ROOT/course_<course_number>/<assignment_title>/Answer_Key/<filename>
        return 'course_{0}-{3}/{1}/Answer_Key/{2}'.format(instance.course.course_number, instance.title, filename, str(instance.course.course_id)[0:6])
    
    def validate_process(value):
        allowed = [0, 1, 2, 3]
        if value not in allowed:
            raise ValidationError(
                _('%(value)s is not an process indicator, it should be either 0, 1 or 2.'),
                params={'value': value},
            )

    assignment              = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name="assignment_grading_profile")
    answer_pdf              = models.FileField(upload_to=answer_path, validators=[FileExtensionValidator(allowed_extensions=['pdf','doc','txt'])], null=True, blank=True)
    regrading_requests      = models.BooleanField(default = True) 
    peergrading             = models.BooleanField(default=False, help_text='Sets whether peergrading should be allowed for the course or not')
    param_mu                = models.FloatField(help_text='Parameter to be set as per the TRUPEQA algorithm', default=16.234)
    param_gm                = models.FloatField(help_text='Parameter to be set as per the TRUPEQA algorithm', default=1.234)
    peerdist                = models.IntegerField(default=6, help_text='This is the number of copies that will be distributed to peers.')
    n_probes                = models.IntegerField(default=20, help_text='These are the number of probes you want to set for this assignment.')
    under_config            = models.IntegerField(default=1, validators=[validate_process])
    under_mapping           = models.IntegerField(default=0, validators=[validate_process])
    under_grading           = models.IntegerField(default=0, validators=[validate_process])
    under_regrading         = models.IntegerField(default=0, validators=[validate_process])
    graded                  = models.IntegerField(default=0, validators=[validate_process])
    probe_mapped            = models.BooleanField(default=False)
    mapping_deadline        = models.DateField(null=True, blank=True)
    probing_deadline        = models.DateField(null=True, blank=True)
    grading_deadline        = models.DateField(null=True, blank=True)
    peergrading_deadline    = models.DateField(null=True, blank=True)
    regrading_deadline      = models.DateField(null=True, blank=True)