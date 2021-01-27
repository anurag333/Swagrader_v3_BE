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
        agp = AssignmentGradingProfile.objects.create(assignment=instance)
        agp.instructor_graders.add(*(instance.course.instructors.all()))
        agp.ta_graders.add(*(instance.course.teaching_assistants.all()))

@receiver(post_save, sender=Assignment)
def save_assign_grading_profile(sender, instance, **kwargs):
    try:
        instance.assignment_grading_profile.save()
    except:
        agp = AssignmentGradingProfile.objects.create(assignment=instance)
        agp.instructor_graders.add(*(instance.course.instructors.all()))
        agp.ta_graders.add(*(instance.course.teaching_assistants.all()))

@receiver(post_save, sender=Assignment)
def create_assign_peergrading_profile(sender, instance, created, **kwargs):
    if created:
        apgp = AssignmentPeergradingProfile.objects.create(assignment=instance)
        apgp.instructor_graders.add(*(instance.course.instructors.all()))
        apgp.ta_graders.add(*(instance.course.teaching_assistants.all()))
        apgp.peergraders.add(*(instance.course.students.all()))

@receiver(post_save, sender=Assignment)
def save_assign_peergrading_profile(sender, instance, **kwargs):
    try:
        instance.assignment_peergrading_profile.save()
    except:
        apgp = AssignmentPeergradingProfile.objects.create(assignment=instance)
        apgp.instructor_graders.add(*(instance.course.instructors.all()))
        apgp.ta_graders.add(*(instance.course.teaching_assistants.all()))
        apgp.peergraders.add(*(instance.course.students.all()))


@receiver(post_save, sender=Question)
def create_question_default_global_rubric(sender, instance, created, **kwargs):
    if created:
        GlobalRubric.objects.create(question=instance, description='Correct', marks=instance.max_marks)
        GlobalRubric.objects.create(question=instance, description='Incorrect', marks=instance.min_marks)

@receiver(post_save, sender=SubQuestion)
def create_subquestion_default_global_rubric(sender, instance, created, **kwargs):
    if created:
        GlobalSubrubric.objects.create(sub_question=instance, description='Correct', marks=instance.max_marks)
        GlobalSubrubric.objects.create(sub_question=instance, description='Incorrect', marks=instance.min_marks)

@receiver(post_save, sender=GlobalRubric)
def create_probe_rubric(sender, instance, created, **kwargs):
    if created:
        ProbeRubric.objects.create(rubric=instance)

@receiver(post_save, sender=GlobalSubrubric)
def create_probe_subrubric(sender, instance, created, **kwargs):
    if created:
        ProbeSubrubric.objects.create(sub_rubric=instance)

@receiver(post_save, sender=GlobalRubric)
def save_probe_rubric(sender, instance, **kwargs):
        instance.probe_rubric.save()

@receiver(post_save, sender=GlobalSubrubric)
def save_probe_subrubric(sender, instance, **kwargs):
        instance.probe_subrubric.save()