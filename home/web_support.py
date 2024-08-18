from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from django.shortcuts import render, get_object_or_404, redirect
from .forms import *

def web_support(request):
    return render(request, 'pages/web_support.html')