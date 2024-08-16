from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import TicketSerializer, TicketLogSerializer, CommentSerializer, FAQSerializer
from django.shortcuts import render, get_object_or_404, redirect
from .forms import *
from django.views.generic import UpdateView
from django.contrib.auth.decorators import login_required
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Q, Exists, OuterRef
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.views.generic import ListView
from django.db.models import ExpressionWrapper, F, DurationField
from django.db.models.functions import Coalesce
from .decorators import staff_required
from django.db.models import Prefetch

class TicketListCreateView(generics.ListCreateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

class TicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

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
#     tickets = Ticket.objects.order_by('-created_at')[:10].prefetch_related(
#     Prefetch('messages', queryset=Message.objects.order_by('created_at'))
# )

    escalated_subquery = TicketLog.objects.filter(
        ticket_id=OuterRef('pk'),
        changed_by__icontains='escalated'
    ).values('id')

    tickets = Ticket.objects.order_by('-created_at')[:10].annotate(
            message_count=Count('messages'),
            is_escalated=Exists(escalated_subquery)
    )

    
    try:
        request_user_support_member = SupportMember.objects.get(user=request.user.id)
        request_user_tickets = all_tickets.filter(assigned_to=request_user_support_member)
        request_user_tickets_count = request_user_tickets.count()
        request_user_open_tickets_count = request_user_tickets.filter(status='open').count()
        request_user_resolved_tickets_count = request_user_tickets.filter(status='resolved').count()
        request_user_closed_tickets_count = request_user_tickets.filter(status='closed').count()
        request_user_pending_tickets_count = request_user_tickets.filter(status='pending').count()
    except SupportMember.DoesNotExist:
        request_user_tickets_count = 0
        request_user_open_tickets_count = 0
        request_user_resolved_tickets_count = 0
        request_user_closed_tickets_count = 0
        request_user_pending_tickets_count = 0
    

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
        'tickets': tickets,
        'request_user_tickets_count': request_user_tickets_count,
        'request_user_open_tickets_count': request_user_open_tickets_count,
        'request_user_resolved_tickets_count': request_user_resolved_tickets_count,
        'request_user_closed_tickets_count': request_user_closed_tickets_count,
        'request_user_pending_tickets_count': request_user_pending_tickets_count,
        'request_user_open_tictes_percentage': calculate_percentage(request_user_open_tickets_count),
        'request_user_resolved_tictes_percentage': calculate_percentage(request_user_resolved_tickets_count),
        'request_user_closed_tictes_percentage': calculate_percentage(request_user_closed_tickets_count),
        'request_user_pending_tictes_percentage': calculate_percentage(request_user_pending_tickets_count),
        
    }

    return render(request, 'pages/index.html', context=context)

@require_GET
@login_required
@staff_required
def get_chart_data(request):
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())
    last_seven_days = [start_of_week + timedelta(days=i) for i in range(7)]
    
    resolved_counts_weekly = []
    open_counts_weekly = []
    closed_counts_weekly = []
    pending_counts_weekly = []

    for day in last_seven_days:
        resolved_count = Ticket.objects.filter(
            status='resolved',
            resolved_at__date=day.date()
        ).count()
        open_count = Ticket.objects.filter(
            status='open',
            created_at__date=day.date()
        ).count()
        closed_count = Ticket.objects.filter(
            status='closed',
            closed_at__date=day.date()
        ).count()
        pending_count = Ticket.objects.filter(
            status='pending',
            created_at__date=day.date()
        ).count()

        resolved_counts_weekly.append(resolved_count)
        open_counts_weekly.append(open_count)
        closed_counts_weekly.append(closed_count)
        pending_counts_weekly.append(pending_count)

    last_nine_months = [(today - timedelta(days=30 * i)).strftime('%b') for i in reversed(range(9))]
    
    resolved_counts_monthly = []
    open_counts_monthly = []
    closed_counts_monthly = []
    pending_counts_monthly = []

    for month in reversed(range(9)):
        start_of_month = (today.replace(day=1) - timedelta(days=30 * month)).replace(day=1)
        end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
        
        resolved_count = Ticket.objects.filter(
            status='resolved',
            resolved_at__range=[start_of_month, end_of_month]
        ).count()
        open_count = Ticket.objects.filter(
            status='open',
            created_at__range=[start_of_month, end_of_month]
        ).count()
        closed_count = Ticket.objects.filter(
            status='closed',
            closed_at__range=[start_of_month, end_of_month]
        ).count()
        pending_count = Ticket.objects.filter(
            status='pending',
            created_at__range=[start_of_month, end_of_month]
        ).count()

        resolved_counts_monthly.append(resolved_count)
        open_counts_monthly.append(open_count)
        closed_counts_monthly.append(closed_count)
        pending_counts_monthly.append(pending_count)

    data = {
        "labels_weekly": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "resolved_counts_weekly": resolved_counts_weekly,
        "open_counts_weekly": open_counts_weekly,
        "closed_counts_weekly": closed_counts_weekly,
        "pending_counts_weekly": pending_counts_weekly,
        
        "labels_monthly": last_nine_months,
        "resolved_counts_monthly": resolved_counts_monthly,
        "open_counts_monthly": open_counts_monthly,
        "closed_counts_monthly": closed_counts_monthly,
        "pending_counts_monthly": pending_counts_monthly,
    }

    return JsonResponse(data)

def ticket_list_by_status(request, status):
    tickets = Ticket.objects.filter(status=status)

    operator = request.GET.get('operator', '=')
    filter_time = request.GET.get('filter_time')

    if filter_time:
        try:
            filter_time = int(filter_time)
            # Convert minutes to a timedelta object
            filter_time_duration = timedelta(minutes=filter_time)
            end_time = now()

            # Use expression to calculate the duration from creation to the end time
            tickets = tickets.annotate(
                time_to_resolve=ExpressionWrapper(
                    F('resolved_at') - F('created_at'),
                    output_field=DurationField()
                )
            )

            if operator == '=':
                tickets = tickets.filter(
                    time_to_resolve=filter_time_duration
                )
            elif operator == '<':
                tickets = tickets.filter(
                    time_to_resolve__lt=filter_time_duration
                )
            elif operator == '>':
                tickets = tickets.filter(
                    time_to_resolve__gt=filter_time_duration
                )
            elif operator == '<=':
                tickets = tickets.filter(
                    time_to_resolve__lte=filter_time_duration
                )
            elif operator == '>=':
                tickets = tickets.filter(
                    time_to_resolve__gte=filter_time_duration
                )
        except ValueError:
            pass  # Ignore if the filter_time is not a valid integer

    return render(request, 'tickets/ticket_list.html', {'tickets': tickets, 'status': status})

def home_view(request):
    return JsonResponse({'message': 'Home!'})

@login_required
@staff_required
def users_list(request):
    users = User.objects.all()
    return render(request, 'pages/users.html', {'users': users})

@login_required
@staff_required
def edit_user(request, id):
    user = get_object_or_404(User, id=id)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')  
    else:
        form = UserForm(instance=user)
    return render(request, 'pages/edit_system_user.html', {'form': form, 'user': user})

@login_required
@staff_required
def edit_support_member(request, id):
    member = get_object_or_404(SupportMember, id=id)
    
    if request.method == 'POST':
        form = SupportMemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            return redirect('support_users_list')  
    else:
        form = SupportMemberForm(instance=member)
    return render(request, 'pages/edit_user.html', {'form': form, 'member': member})

@login_required
@staff_required
def profile_view(request):
    user = request.user
    return render(request, 'pages/profile.html', {'user': user})

@login_required
@staff_required
def support_users_list(request):
    support_members = SupportMember.objects.all()
    return render(request, 'pages/tables.html', {'support_members': support_members})

def support_member_tickets(request, member_id):
    try:
        member = SupportMember.objects.get(id=member_id)
    except SupportMember.DoesNotExist:
        return HttpResponse("Support Member not found")

    tickets = Ticket.objects.filter(assigned_to=member.id)
    for ticket in tickets:
        if ticket.status in ['resolved', 'closed']:
            if ticket.resolved_at:
                time_taken = ticket.resolved_at - ticket.created_at
            else:
                time_taken = ticket.closed_at - ticket.created_at
            ticket.time_taken = time_taken
        else:
            ticket.time_taken = None

    return render(request, 'tickets/tickets_by_assignee.html', {'tickets': tickets, 'member': member})

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

def ticket_detail_view(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    messages = Message.objects.filter(ticket_id=ticket_id)
    logs = TicketLog.objects.filter(ticket=ticket).order_by('timestamp')
    escalation_log_exists = logs.filter(changed_by__icontains='escalated').exists()
    context = {
        'ticket': ticket or None,
        'messages': messages or None,
        'support_members': SupportMember.objects.all() or None,
        'logs': logs or None,
        'escalated': escalation_log_exists
    }
    return render(request, 'tickets/ticket_detail.html', context)

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

