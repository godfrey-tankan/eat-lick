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
from .helpers import format_phone_number
from a_bot.responses import *

@csrf_exempt
def web_support(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        phone = data.get('phone')
        message = data.get('message')
        if phone:
            phone = format_phone_number(phone)
        try:
            get_inquirer = Inquirer.objects.get(phone_number=phone)
        except Inquirer.DoesNotExist:
            get_inquirer = None
        if get_inquirer:
            if get_inquirer.user_mode == NAMES_MODE:
                get_inquirer.username = message
                get_inquirer.user_mode = BRANCH_MODE
                get_inquirer.save()
                return JsonResponse({'success': True, 'message': f'Hello {message}, which branch are you inquiring from?'})
            elif get_inquirer.user_mode == BRANCH_MODE:
                get_inquirer.branch = message
                get_inquirer.user_mode = WAITING_MODE
                get_inquirer.save()
                return JsonResponse({'success': True, 'message': f'Hello {get_inquirer.username}, how can we help you today?.'})
            get_inquirer.user_mode = INQUIRY_MODE
            get_inquirer.save()
            return JsonResponse({'success': True, 'message': f'Hello {get_inquirer.username.split()[0]}, how can we help you today?.'})
        else:
            Inquirer.objects.create(phone_number=phone,user_mode =NAMES_MODE)
            return JsonResponse({'success': True, 'message': f'We are creating an account for you. Please Please provide your names'})
        if not phone:
            return JsonResponse({'success': False, 'error': 'Phone number is required.'})
        return JsonResponse({'success': True, 'message': f'Welcome! Your phone number {phone} has been registered.'})

        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    return render(request, 'pages/web_support.html')