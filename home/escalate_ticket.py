from django.shortcuts import get_object_or_404, redirect, render, HttpResponse
from .models import Ticket, SupportMember, Message,TicketLog
from django.contrib.auth.decorators import login_required
from a_bot.views import web_messaging

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
                changed_by=f'Ticket escalated to {assign_to.username}',
                status=ticket.status
            )
            
            if assign_to.id == request.user:
                
                message_content = request.POST.get('message_content')
                if message_content:
                    Message.objects.create(
                        ticket=ticket,
                        content=message_content,
                        support_member=request.user.id
                    )

        return redirect('ticket_detail', ticket_id=ticket.id)
    return redirect('ticket_list')

@login_required
def send_message(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    support_member = SupportMember.objects.get(id=request.user.id)
    
    if support_member and request.method == 'POST':
        message_content = request.POST.get('message_content')
        if message_content:
            Message.objects.create(
                ticket_id=ticket,
                content=message_content,
                support_member=support_member
            )
            web_messaging(ticket.id,message_content)
        

    return render(request, 'ticktes/ticket_detail.html', {'ticket': ticket,'messages':Message.objects.filter(ticket_id=ticket)})

