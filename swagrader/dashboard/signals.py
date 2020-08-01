from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *


@receiver(post_save, sender=Course)
def create_course_metadata(sender, instance, created, **kwargs):
    if created:
        CourseMetadata.objects.create(course=instance)

@receiver(post_save, sender=Course)
def save_course_metadata(sender, instance, **kwargs):
    try:
        instance.course_metadata.save()
    except:
        CourseMetadata.objects.create(course=instance)

@receiver(post_save, sender=Assignment)
def create_assign_grading_profile(sender, instance, created, **kwargs):
    if created:
        AssignmentGradingProfile.objects.create(assignment=instance)

@receiver(post_save, sender=Assignment)
def save_assign_grading_profile(sender, instance, **kwargs):
    try:
        instance.assignment_grading_profile.save()
    except:
        AssignmentGradingProfile.objects.create(assignment=instance)

@receiver(post_save, sender=Assignment)
def create_assign_peergrading_profile(sender, instance, created, **kwargs):
    if created:
        AssignmentPeergradingProfile.objects.create(assignment=instance)

@receiver(post_save, sender=Assignment)
def save_assign_peergrading_profile(sender, instance, **kwargs):
    try:
        instance.assignment_peergrading_profile.save()
    except:
        AssignmentPeergradingProfile.objects.create(assignment=instance)
