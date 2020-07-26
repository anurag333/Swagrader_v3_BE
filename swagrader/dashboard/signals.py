from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Course, CourseMetadata, Roster

@receiver(post_save, sender=Course)
def create_course_metadata(sender, instance, created, **kwargs):
    if created:
        print('got the signal, creating the metadata for the course ', instance)
        CourseMetadata.objects.create(course=instance)

# @receiver(post_save, sender=Course)
# def save_course_metadata(sender, instance, **kwargs):
#     print('saving the metadata also')
#     try:
#         instance.course_metadata.save()
#     except:
#         CourseMetadata.objects.create(course=instance)