from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *

@receiver(post_save, sender=Course)
def create_course_metadata(sender, instance, created, **kwargs):
    if created:
        print('got the signal, creating the metadata for the course ', instance)
        CourseMetadata.objects.create(course=instance)

@receiver(post_save, sender=Course)
def save_course_metadata(sender, instance, **kwargs):
    print('saving the metadata also')
    try:
        instance.course_metadata.save()
    except:
        CourseMetadata.objects.create(course=instance)

@receiver(post_save, sender=Assignment)
def create_assign_grading_profile(sender, instance, created, **kwargs):
    if created:
        print('got the signal, creating the profile for the assign ', instance)
        AssignmentGradingProfile.objects.create(assignment=instance)

@receiver(post_save, sender=Assignment)
def save_course_metadata(sender, instance, **kwargs):
    print('saving the assign profile also')
    try:
        instance.assignment_grading_profile.save()
    except:
        AssignmentGradingProfile.objects.create(course=instance)
