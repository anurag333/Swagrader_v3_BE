from django import forms
from .models import SwagraderUser
from django.contrib.auth.forms import UserCreationForm


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=2000)

    class Meta:
        model = SwagraderUser
        fields = ('email', 'first_name', 'last_name',
                  'institute_id', 'password1', 'password2')
