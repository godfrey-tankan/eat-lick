from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from django.shortcuts import render, get_object_or_404, redirect
from .forms import *
import json
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def web_support(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        phone = data.get('phone')

        # Validate the phone number (optional)
        if not phone:
            return JsonResponse({'success': False, 'error': 'Phone number is required.'})

        # Process the phone number (e.g., save to the database, validate, etc.)
        # For now, just return a success response with a welcome message
        return JsonResponse({'success': True, 'message': f'Welcome! Your phone number {phone} has been registered.'})

        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    return render(request, 'pages/web_support.html')