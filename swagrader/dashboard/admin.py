from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Course)
admin.site.register(CourseMetadata)
admin.site.register(Roster)
admin.site.register(Assignment)
admin.site.register(AssignmentGradingProfile)
admin.site.register(Question)
admin.site.register(SubQuestion)
admin.site.register(AssignmentSubmission)
admin.site.register(QuestionSubmission)