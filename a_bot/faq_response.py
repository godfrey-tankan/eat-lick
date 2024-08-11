# from home.models import *
# from .views import create_ticket
# from django.http import JsonResponse
# def handle_inquiry(request):
#     response = request.POST.get('response')
#     name = request.POST.get('name')

#     if faq := FAQ.objects.filter(question__icontains=response).first():
#         ticket = Ticket.objects.create(
#             title=f"FAQ Match for {name}",
#             description=faq.answer,
#             created_by=request.user,
#             status='resolved'
#         )
#         return JsonResponse({"status": "FAQ match found", "answer": faq.answer, "ticket_id": ticket.id})
#     return create_ticket(request, response, name)
