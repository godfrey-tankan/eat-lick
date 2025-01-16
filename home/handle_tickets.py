from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Ticket, Inquirer, SupportMember, Branch
from .forms import NewTicketForm
import json
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

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
            ticket.status = 'resolved'
            ticket.resolved_at=timezone.now()
            ticket.save()  # Save the ticket
            print("ticket saved.....")
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": form.errors})

    return JsonResponse({"success": False, "message": "Invalid request"})