from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm


@csrf_exempt
def custom_login(request):
    if request.method == 'POST':
        print('logiing in,......')
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect('/')  # Redirect to the home page or another page of your choice
        else:
            pass
    # return redirect('login')
    

