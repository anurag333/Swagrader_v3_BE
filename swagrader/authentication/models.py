from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from .managers import SwagraderUserManager
from rest_framework.response import Response
from allauth.account.models import EmailAddress

class EmailNamespace(models.Model):
    namespace = models.CharField(max_length=30)

    def __str__(self):
        return self.namespace

class SwagraderUser(AbstractUser):
    username = None
    email = models.EmailField(('email address'), unique=True)
    institute_id = models.BigIntegerField(null=True, blank=True)
    global_instructor_privilege = models.BooleanField(default=False)
    global_ta_privilege = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = SwagraderUserManager()

    def save(self, *args, **kwargs):
        namespace = self.email[self.email.rfind('@')+1 :]
        if not EmailNamespace.objects.filter(namespace=namespace).exists():
            if not self.is_superuser:
                raise ValidationError('Email should have the admin defined namespace, kindly contact admin for more details')
                # return Response({'message': 'Email should have the admin defined namespace, kindly contact admin for more details'}, status=403)
            else:
                ns = EmailNamespace.objects.create(namespace=namespace)
        super(SwagraderUser, self).save(*args, **kwargs)

        eaddr = EmailAddress(email=self.email, user=self, verified=True, primary=True)
        eaddr.save()

    def __str__(self):
        if self.first_name or self.last_name:
            return '{rn}: {fn} {ln}'.format(rn=self.institute_id, fn=self.first_name, ln=self.last_name)
    
        return self.email
