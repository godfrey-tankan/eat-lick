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
from a_bot.views import alert_support_members

@csrf_exempt
def web_support(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        phone = data.get('phone')
        message = data.get('message', '')
        if phone:
            phone = format_phone_number(phone)
        try:
            get_inquirer = Inquirer.objects.get(phone_number=phone)
        except Inquirer.DoesNotExist:
            get_inquirer = None
        if get_inquirer:
            for msg in resolve_ticket_responses:
                if msg in message:
                    ticket_in_pg = Ticket.objects.filter(created_by=get_inquirer, status__in=['open', 'pending']).last()
                    alert_support_members(get_inquirer.username,ticket_in_pg, message,True)
                    return JsonResponse({'success': True, 'message': f'Hello {get_inquirer.username.split()[0]}, your inquiry has been resolved. Thank you for reaching out.'})
            if get_inquirer.user_mode == INQUIRY_MODE:
                return create_web_inquiry(get_inquirer, message)
            if get_inquirer.user_mode == NAMES_MODE:
                get_inquirer.username = message
                get_inquirer.user_mode = BRANCH_MODE
                get_inquirer.save()
                return JsonResponse({'success': True, 'message': f'Hello {message}, which branch are you inquiring from?'})
            elif get_inquirer.user_mode == BRANCH_MODE:
                get_inquirer.branch = message
            get_inquirer.user_mode = INQUIRY_MODE
            get_inquirer.save()
            return JsonResponse({'success': True, 'message': f'Hello {get_inquirer.username.split()[0]}, how can we help you today?.'})
        else:
            Inquirer.objects.create(phone_number=phone,user_mode =NAMES_MODE)
            return JsonResponse({'success': True, 'message': 'Hello, Please provide your full name.'})
        
    return render(request, 'pages/web_support.html')

def create_web_inquiry(inquirer, message):
    try:
        pending_tickets = Ticket.objects.filter(created_by=inquirer, status__in=['open', 'pending'])
    except Ticket.DoesNotExist:
        pending_tickets = None
    if pending_tickets:
        if len(message) < 5:
            return JsonResponse({'success': True, 'message': f'Hello {inquirer.username.split()[0]}, you have a pending ticket. Please wait for a support member to respond. You just reply with #done or #resolved when you are helped.'})
        new_msg = Message.objects.create(ticket_id=pending_tickets.last(),inquirer=inquirer, content=message)
        return JsonResponse({'success': True, 'message': f'Someone is attending to your inquiry. Please wait for a response.You can reply with #done or #resolved anytime when you are helped.'})
    ticket=Ticket.objects.create(title=message.split()[0], created_by=inquirer,description=message, status='open')
    TicketLog.objects.create(ticket=ticket, status=ticket.status, changed_by=inquirer)
    alert_support_members(inquirer.username,ticket, message)
    return JsonResponse({'success': True, 'message': f'Hello {inquirer.username.split()[0]}, your inquiry #{ticket.id} has been received. A support member will be with you shortly.'})