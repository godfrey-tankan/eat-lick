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
                    ticket_in_pg = Ticket.objects.filter(created_by=get_inquirer,ticket_mode='other', status__in=['open', 'pending']).last()
                    if ticket_in_pg:
                        alert_support_members(get_inquirer.username,ticket_in_pg,None,True)
                        return JsonResponse({'success': True, 'message': f'Hello {get_inquirer.username.split()[0]}, your inquiry has been resolved. Thank you for reaching out.'})
                    return JsonResponse({'success': True, 'message': f'Hello {get_inquirer.username.split()[0]}, you do not have any pending inquiries.'})
            for msg in thank_you_messages:
                if msg in message:
                    ticket_in_pg = Ticket.objects.filter(created_by=get_inquirer,ticket_mode='other', status__in=['open', 'pending']).last()
                    if ticket_in_pg:
                        alert_support_members(get_inquirer.username,ticket_in_pg,None,True)
                        return JsonResponse({'success': True, 'message': f'Hello {get_inquirer.username.split()[0]}, your inquiry has been resolved. Thank you for reaching out.'})
                    return JsonResponse({'success': True, 'message': f'Hello {get_inquirer.username.split()[0]}, you do not have any pending inquiries.'})
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
        pending_tickets = Ticket.objects.filter(created_by=inquirer,ticket_mode='other', status__in=['open', 'pending'])
    except Ticket.DoesNotExist:
        pending_tickets = None
    for greeting in greeting_messages:
        if greeting == message:
            return JsonResponse({'success': True, 'message': f'Golden greetings {inquirer.username.split()[0]}, how can we help you today?'})
    if pending_tickets:
        if len(message) < 5:
            return JsonResponse({'success': True, 'message': f'Hello {inquirer.username.split()[0]}, Welcome back to your pending Inquiry, #{pending_tickets.last().id} \n\nWhat do you want to say?.\nPlease reply with #done or #resolved when you are or have been helped.'})
        new_msg = Message.objects.create(ticket_id=pending_tickets.last(),inquirer=inquirer, content=message)
        if pending_tickets.last().ticket_mode =='other':
            alert_support_members('name',pending_tickets.last(), message)
            return JsonResponse({'success': True, 'message': f'Inquiry #{pending_tickets.last().id} is now active.'})
        return JsonResponse({'success': True, 'message': f'Someone is attending to your inquiry. Please wait for a response.You can reply with #done or #resolved anytime when you are helped.'})
    if len(message) < 5:
        return JsonResponse({'success': True, 'message': f'Hello {inquirer.username.split()[0]}, please provide a detailed description of your inquiry.'})
    description = 'Source Web: ' + message
    ticket=Ticket.objects.create(title=f"Inquiry from Web", created_by=inquirer,branch_opened=inquirer.branch,description=description, status='open')
    TicketLog.objects.create(ticket=ticket, status=ticket.status, changed_by=inquirer)
    if ticket.assigned_to:
        return alert_support_members(inquirer.username,ticket, message)
    alert_support_members(inquirer.username,ticket, None)
    return JsonResponse({'success': True, 'message': f'Hello {inquirer.username.split()[0]}, your inquiry #{ticket.id} has been received. A support member will be with you shortly.'})