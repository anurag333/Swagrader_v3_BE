from allauth.account.adapter import DefaultAccountAdapter
from .models import EmailNamespace
from django.forms import ValidationError

class SwagraderAdapter(DefaultAccountAdapter):
    
    def clean_email(self, email):
        namespace = email[email.rfind('@')+1 :]
        if not EmailNamespace.objects.filter(namespace=namespace).exists():
            raise ValidationError(('Email should have the admin defined namespace, kindly contact admin for more details'))
        return email