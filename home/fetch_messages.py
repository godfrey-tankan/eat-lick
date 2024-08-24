from django.shortcuts import get_object_or_404, redirect, render, HttpResponse
from .models import Ticket, SupportMember, Message,TicketLog
from django.contrib.auth.decorators import login_required
from a_bot.views import web_messaging
from django.http import JsonResponse
from django.utils import timezone


@login_required
def fetch_messages(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    messages = Message.objects.filter(ticket_id=ticket).order_by('created_at')
    message_list = [
        {
            'content': message.content,
            'created_at': timezone.localtime(message.created_at).strftime('%d/%m/%Y %H:%M'),
            'username': message.inquirer.username if message.inquirer else message.support_member.username,
            'inquirer': bool(message.inquirer),
        }
        for message in messages
    ]
    return JsonResponse({'messages': message_list})
