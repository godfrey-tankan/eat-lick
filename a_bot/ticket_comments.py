import json
from django.http import JsonResponse
from a_home.models import *

def add_comment(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    content = request.POST.get('content')
    
    comment = Comment.objects.create(
        ticket=ticket,
        user=request.user,
        content=content
    )
    return JsonResponse({"status": "Comment added", "comment_id": comment.id})
