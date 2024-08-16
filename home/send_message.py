# @login_required
# def send_message(request, ticket_id):
#     ticket = get_object_or_404(Ticket, id=ticket_id)
    
#     if request.method == 'POST':
#         message_content = request.POST.get('message_content')
#         if message_content:
#             Message.objects.create(
#                 ticket=ticket,
#                 content=message_content,
#                 support_member=request.user.supportmember
#             )

#         return redirect('ticket_detail', ticket_id=ticket.id)

#     return redirect('ticket_list')
