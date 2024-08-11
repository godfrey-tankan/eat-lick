from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import HttpResponse,render,redirect

def logout_view(request):
    if request.method not in ['POST', 'GET']:
        return HttpResponse(status=405)
    logout(request)
    return redirect('/')