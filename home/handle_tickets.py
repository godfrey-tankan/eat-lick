from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Ticket, Inquirer, SupportMember, Branch, TicketLog
from .forms import NewTicketForm
import json
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from a_bot.views import alert_support_members


# API endpoint to submit a ticket
@csrf_exempt
@login_required
def create_ticket(request):
    if request.method == 'GET':
        inquirers = list(Inquirer.objects.filter(is_active=True).values('id', 'username')) 
        support_members = list(SupportMember.objects.filter(is_active=True).values('id', 'username')) 
        branches = list(Branch.objects.all().values('id', 'name')) 

        return JsonResponse({
            'inquirers': inquirers,
            'support_members': support_members,
            'branches': branches,
        })

    elif request.method == 'POST':
        form = NewTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.status = 'pending'
            ticket.save()
            TicketLog.objects.create(ticket=ticket, changed_by='Manually created ticket', status='pending')
            check_pending_tickets = Ticket.objects.filter(status='pending',ticket_mode='other').first()
            if check_pending_tickets:
                ticket.ticket_mode = 'queued'
                ticket.queued_at = timezone.now()
                ticket.save()
                message = f"🚨 Hello {ticket.assigned_to.username.title()}, ticket #{ticket.id} ({ticket.description}) has been assigned to you, and it`s now in your queue."
            else:
                message = f"🚨 Hello {ticket.assigned_to.username.title()}, ticket #{ticket.id} - {ticket.branch_opened}\n Description: ({ticket.description}) \n Inquirer: {ticket.created_by.username.title()} \nhas been assigned to you, start assisting the inquirer now or mark it as resolved if the issue has been dealt with."
            alert_support_members(ticket.assigned_to.username,ticket,message)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": form.errors})

    return JsonResponse({"success": False, "message": "Invalid request"})