from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import SwagraderUserManager

class SwagraderUser(AbstractUser):
    username = None
    email = models.EmailField(('email address'), unique=True)
    institute_id = models.BigIntegerField(null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = SwagraderUserManager()
    
    def __str__(self):
        return self.email

