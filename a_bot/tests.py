from django.test import TestCase
from a_home.models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def test(request,ticket_id):
    try:
        ticket_id = int(ticket_id)
    except:
        return JsonResponse({'message':'Invalid ticket id'}, status=400,safe=False)
    try:
        if check_ticket := Ticket.objects.get(id=ticket_id):
            is_ticket_open = check_ticket.status.lower() == 'open'
            return JsonResponse({'message':'Ticket found'}, status=200,safe=False)
        else:
            return "wrong ticket id"
    except Ticket.DoesNotExist:
        return JsonResponse({'message':'Ticket not found'}, status=404,safe=False)
   
# Create your tests here.
