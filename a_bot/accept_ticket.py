# import contextlib
# from django.views.decorators.csrf import csrf_exempt
# from django.shortcuts import render
# from django.http import JsonResponse
# from a_home.models import *
# from django.contrib.auth.models import Group
# from .responses import *
# from .views import get_text_message_input, send_message

# def handle_inquiry(wa_id, response, name):
#     ticket = Ticket.objects.create(
#         title=f"Inquiry from {name}",
#         description=response,
#         created_by=wa_id[0], 
#         status='open'
#     )
#     # Log the ticket creation
#     TicketLog.objects.create(
#         ticket=ticket,
#         status='open',
#         changed_by=wa_id[0]
#     )
#     # Broadcast to support members
#     with contextlib.suppress(SupportMember.DoesNotExist):
#         support_members = SupportMember.objects.all()
#         for support_member in support_members:
#             user_mobile = support_member.phone_number
#             support_member.user_mode = ACCEPT_TICKET_MODE
#             support_member.save()
#             message=accept_ticket_response.format(support_member.username,name,ticket.id, ticket.description)
#             try:
#                 data = get_text_message_input(user_mobile, message, None)
#                 response = send_message(data)
#             except Exception as e:
#                 response = "error sending messages"
        
#     response = 'Thank you for contacting us. A support member will be assisting you shortly.'

#     return response

# @csrf_exempt
# def accept_ticket(wa_id,name, ticket_id):
#     support_member = wa_id[0]
#     try:
#         ticket = Ticket.objects.get(id=ticket_id, status='open')
#         ticket.assigned_to = support_member
#         ticket.status = 'pending'
#         ticket.save()
        
#         # Log the status change
#         TicketLog.objects.create(
#             ticket=ticket,
#             status='pending',
#             changed_by=support_member
#         )
        
#         return f"Ticket #{ticket.id} assigned to {name}"
#     except Ticket.DoesNotExist:
#         return "Ticket not available or already assigned"
