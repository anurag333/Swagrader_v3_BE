from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from .forms import *
from django.contrib import messages
# Create your views here.


@api_view(['GET', 'POST'])
def signup(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "user created successfully")
            return redirect("login")
        else:
            messages.warning(request, "some feilds are not valid")
    else:
        form = RegistrationForm()
    context = {"form": form, }
    return render(request, "signup.html", context)
