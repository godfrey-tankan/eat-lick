from django.shortcuts import get_object_or_404, redirect, render, HttpResponse
from .models import Ticket, SupportMember, Message,TicketLog
from django.contrib.auth.decorators import login_required
from a_bot.views import web_messaging
from django.http import JsonResponse
from django.utils import timezone

@login_required
def escalate_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        assign_to_id = request.POST.get('assign_to')
        if assign_to_id:
            assign_to = SupportMember.objects.get(id=assign_to_id)
            ticket.assigned_to = assign_to
            ticket.save()
            TicketLog.objects.create(
                ticket=ticket,
                changed_by=f'{ticket.assigned_to}, Ticket escalated to {assign_to.username}',
                status=ticket.status
            )
            
            web_messaging(ticket.id,None,True,assign_to_id)
                    
        return redirect('ticket_detail', ticket_id=ticket.id)
    return redirect('ticket_list')

@login_required
def send_message(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    support_member = SupportMember.objects.get(id=request.user.id)
    
    if support_member and request.method == 'POST':
        message_content = request.POST.get('message_content')
        if message_content:
            new_message = Message.objects.create(
                ticket_id=ticket,
                content=message_content,
                support_member=support_member,
                created_at=timezone.now()
            )
            web_messaging(ticket.id, message_content)
            return redirect('ticket_detail', ticket_id=ticket.id)
    
    return JsonResponse({'error': 'Invalid request or support member not found'}, status=400)