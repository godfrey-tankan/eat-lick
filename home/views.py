from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import TicketSerializer, TicketLogSerializer, CommentSerializer, FAQSerializer
from django.shortcuts import render, get_object_or_404, redirect
from .forms import TicketForm, CommentForm
from django.views.generic import UpdateView
from django.contrib.auth.decorators import login_required
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from .models import Ticket
from django.db.models import Count, Q

@login_required
def index(request):
    # Get all tickets
    all_tickets = Ticket.objects.all()
    total_tickets = all_tickets.count()

    open_tickets_count = all_tickets.filter(status='open').count()
    closed_tickets_count = all_tickets.filter(status='closed').count()
    pending_tickets_count = all_tickets.filter(status='pending').count()
    resolved_tickets_count = all_tickets.filter(status='resolved').count()

    def calculate_percentage(count):
        return round((count / total_tickets * 100), 2) if total_tickets > 0 else 0

    # Get support members who resolved more than 5 tickets
    active_support_members = SupportMember.objects.filter(
        username__in=Ticket.objects.filter(
            status='resolved'
        ).values('assigned_to')
    ).annotate(
        resolved_tickets_count=Count('username')
    ).filter(
        resolved_tickets_count__gt=1
    )

    context = {
        "tickets_count": total_tickets,
        "open_tickets_count": open_tickets_count,
        "closed_tickets_count": closed_tickets_count,
        "pending_tickets_count": pending_tickets_count,
        "resolved_tickets_count": resolved_tickets_count,
        "open_tickets_percentage": calculate_percentage(open_tickets_count),
        "closed_tickets_percentage": calculate_percentage(closed_tickets_count),
        "pending_tickets_percentage": calculate_percentage(pending_tickets_count),
        "resolved_tickets_percentage": calculate_percentage(resolved_tickets_count),
        "active_support_members": active_support_members or 0,
    }

    return render(request, 'pages/index.html', context=context)


# Create your views here.
def home_view(request):
    return JsonResponse({'message': 'Home!'})

# Ticket Views
class TicketListCreateView(generics.ListCreateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

class TicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

# TicketLog Views
class TicketLogListCreateView(generics.ListCreateAPIView):
    queryset = TicketLog.objects.all()
    serializer_class = TicketLogSerializer
    permission_classes = [IsAuthenticated]

class TicketLogDetailView(generics.RetrieveAPIView):
    queryset = TicketLog.objects.all()
    serializer_class = TicketLogSerializer
    permission_classes = [IsAuthenticated]

class TicketDeleteView(DeleteView):
    model = Ticket
    template_name = 'ticket_confirm_delete.html' 
    success_url = reverse_lazy('ticket-list')  

class TicketEditView(UpdateView):
    model = Ticket
    fields = ['title', 'description', 'status', 'assigned_to'] 
    template_name = 'your_template.html'
    success_url = '/tickets/'

class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

class FAQListCreateView(generics.ListCreateAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [IsAuthenticated]

class FAQDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [IsAuthenticated]
    
def ticket_list(request):
    tickets = Ticket.objects.all()
    return render(request, 'tickets/ticket_list.html', {'tickets': tickets})

def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.user = request.user
            comment.save()
            return redirect('ticket-detail', pk=ticket.pk)
    else:
        form = CommentForm()
    return render(request, 'tickets/ticket_detail.html', {'ticket': ticket, 'form': form})

def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            return redirect('ticket-list')
    else:
        form = TicketForm()
    return render(request, 'tickets/create_ticket.html', {'form': form})

