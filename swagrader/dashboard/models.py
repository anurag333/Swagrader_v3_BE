from django.db import models
from django.conf import settings
import uuid

class Course(models.Model):
    """
    Course schema for Swagrader.
    """
    course_id           = models.UUIDField(default = uuid.uuid4, editable = False, primary_key = True)
    instructors         = models.ManyToManyField(settings.AUTH_USER_MODEL, 'instructed_courses')
    students            = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_courses', blank=True)
    teaching_assistants   = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name = 'assisted_courses', blank=True)
    course_number       = models.CharField(max_length = 6)
    course_title        = models.CharField(max_length = 40)
    term                = models.CharField(max_length = 6, choices = (('Summer','Summer'),('Winter','Winter'),('Spring','Spring'),('Fall','Fall')))
    year                = models.IntegerField()
    created             = models.DateField(auto_now_add=True)
    entry_key           = models.CharField(editable = False, max_length = 7)
    entry_restricted    = models.BooleanField(default = False)

    def __str__(self):
        return '{0}: {1}'.format(self.course_number, self.course_title)



