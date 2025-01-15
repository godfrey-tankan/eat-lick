from django.http import JsonResponse
from django.shortcuts import render
from .models import Ticket, Inquirer, SupportMember
from .forms import TicketNewForm
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

# API endpoint to submit a ticket
@csrf_exempt
@login_required
def api_create_ticket(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Ensure the data includes required fields
        required_fields = ['title', 'description', 'branch', 'status', 'assigned_to']
        if not all(field in data for field in required_fields):
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

        # Get the inquirer (logged-in user) and assigned support member
        try:
            inquirer = Inquirer.objects.get(user=request.user)
            assigned_to = SupportMember.objects.get(id=data['assigned_to'])
        except Inquirer.DoesNotExist or SupportMember.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Inquirer or Support Member not found'}, status=400)

        # Create the new ticket
        ticket = Ticket.objects.create(
            title=data['title'],
            description=data['description'],
            branch_opened=data['branch'],
            status=data['status'],
            assigned_to=assigned_to,
            created_by=inquirer
        )

        # Respond with the created ticket's ID
        return JsonResponse({'status': 'success', 'ticket_id': ticket.id})

    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


def get_support_members(request):
    members = SupportMember.objects.all().values('id', 'username', 'phone_number')
    return JsonResponse({'members': list(members)})