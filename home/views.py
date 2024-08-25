from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from django.shortcuts import render, get_object_or_404, redirect
from .forms import *
from django.views.generic import UpdateView
from django.contrib.auth.decorators import login_required
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Q, Exists, OuterRef,Subquery
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.views.generic import ListView
from django.db.models import ExpressionWrapper, F, DurationField
from django.db.models.functions import Coalesce
from .decorators import staff_required
from django.db.models import Prefetch
from rest_framework.decorators import api_view
from django.db.models import Count, Q, FloatField, ExpressionWrapper, F, Value, Avg
from django.db.models.functions import Cast, Coalesce
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
    all_tickets=total_tickets=active_support_members=0
    request_user_tickets_count = request_user_open_tickets_count = request_user_resolved_tickets_count = request_user_closed_tickets_count = request_user_pending_tickets_count = 0
    

    all_tickets = Ticket.objects.all()
    # if request.user.is_superuser:
    # else:
    #     support_member = SupportMember.objects.filter(user=request.user).first()
    #     if support_member:
    #         all_tickets = Ticket.objects.filter(assigned_to=support_member)
    open_tickets_count = closed_tickets_count = pending_tickets_count = resolved_tickets_count = 0
    if all_tickets:
        total_tickets = all_tickets.count()
        open_tickets_count = all_tickets.filter(status='open').count()
        closed_tickets_count = all_tickets.filter(status='closed').count()
        pending_tickets_count = all_tickets.filter(status='pending').count()
        resolved_tickets_count = all_tickets.filter(status='resolved').count()

        

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
            ticket=OuterRef('pk'),
            changed_by__icontains='escalated'
        ).values('id')

        tickets = all_tickets.order_by('-created_at')[:10].annotate(
                message_count=Count('messages'),
                is_escalated=Exists(escalated_subquery),
                attended_at=Subquery(
                    TicketLog.objects.filter(
                        ticket=OuterRef('pk'),
                        status__icontains='pending'
                    ).values('timestamp')[:1]
                )
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
            request_user_tickets=None
            request_user_support_member=None
            
        # support_members = get_support_members_stats()
        # print(support_members)
        # for sp in support_members:
        #     print(sp)
    def calculate_percentage(count):
            return round((count / total_tickets * 100), 2) if total_tickets > 0 else 0
    
    context = {
        'sp': get_support_members_stats(request),
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
        'support_members': SupportMember.objects.all(),
        'branches': Branch.objects.all(),
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

def get_support_members_stats(request):
    if request.user.is_superuser:
        support_members = SupportMember.objects.annotate(
            total_resolved=Count('assigned_tickets', filter=Q(assigned_tickets__status='resolved')),
            total_closed_tickets=Count('assigned_tickets', filter=Q(assigned_tickets__status='closed')),
            total_pending_tickets=Count('assigned_tickets', filter=Q(assigned_tickets__status='pending')),
            total_assigned_tickets=Count('assigned_tickets'),
            average_rating=Avg(Cast('assigned_tickets__support_level', FloatField())),
            percentage_resolved=ExpressionWrapper(
                Coalesce(Count('assigned_tickets', filter=Q(assigned_tickets__status='resolved')), 0) * 100.0 /
                Coalesce(Count('assigned_tickets'), 1),
                output_field=FloatField()
            ),
            percentage_pending=ExpressionWrapper(
                Coalesce(Count('assigned_tickets', filter=Q(assigned_tickets__status='pending')), 0) * 100.0 /
                Coalesce(Count('assigned_tickets'), 1),
                output_field=FloatField()
            ),
            percentage_closed=ExpressionWrapper(
                Coalesce(Count('assigned_tickets', filter=Q(assigned_tickets__status='closed')), 0) * 100.0 /
                Coalesce(Count('assigned_tickets'), 1),
                output_field=FloatField()
            ),
            percentage_expired=ExpressionWrapper(
                Coalesce(Count('assigned_tickets', filter=Q(assigned_tickets__status='expired')), 0) * 100.0 /
                Coalesce(Count('assigned_tickets'), 1),
                output_field=FloatField()
            )
        ).order_by('-total_resolved')
    else:
        support_members = SupportMember.objects.filter(user=request.user).annotate(
            total_resolved=Count('assigned_tickets', filter=Q(assigned_tickets__status='resolved')),
            total_closed_tickets=Count('assigned_tickets', filter=Q(assigned_tickets__status='closed')),
            total_pending_tickets=Count('assigned_tickets', filter=Q(assigned_tickets__status='pending')),
            total_assigned_tickets=Count('assigned_tickets'),
            average_rating=Avg(Cast('assigned_tickets__support_level', FloatField())),
            percentage_resolved=ExpressionWrapper(
                Coalesce(Count('assigned_tickets', filter=Q(assigned_tickets__status='resolved')), 0) * 100.0 /
                Coalesce(Count('assigned_tickets'), 1),
                output_field=FloatField()
            ),
            percentage_pending=ExpressionWrapper(
                Coalesce(Count('assigned_tickets', filter=Q(assigned_tickets__status='pending')), 0) * 100.0 /
                Coalesce(Count('assigned_tickets'), 1),
                output_field=FloatField()
            ),
            percentage_closed=ExpressionWrapper(
                Coalesce(Count('assigned_tickets', filter=Q(assigned_tickets__status='closed')), 0) * 100.0 /
                Coalesce(Count('assigned_tickets'), 1),
                output_field=FloatField()
            ),
            percentage_expired=ExpressionWrapper(
                Coalesce(Count('assigned_tickets', filter=Q(assigned_tickets__status='expired')), 0) * 100.0 /
                Coalesce(Count('assigned_tickets'), 1),
                output_field=FloatField()
            )
        ).order_by('-total_resolved')
    
        

    return support_members

@require_GET
@login_required
def get_chart_data(request):
    today = timezone.now()  # Use timezone-aware now
    start_of_week = today - timedelta(days=today.weekday())
    last_seven_days = [start_of_week + timedelta(days=i) for i in range(7)]
    
    resolved_counts_weekly = []
    open_counts_weekly = []
    closed_counts_weekly = []
    pending_counts_weekly = []
    last_nine_months = [(today - timedelta(days=30 * i)).strftime('%b') for i in reversed(range(9))]
    resolved_counts_monthly = []
    open_counts_monthly = []
    closed_counts_monthly = []
    pending_counts_monthly = []
    
    # if request.user.is_superuser:
    for day in last_seven_days:
        day_start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        day_end = day_start + timedelta(days=1)  # The end of the day
        
        resolved_counts_weekly.append(Ticket.objects.filter(
            status='resolved',
            resolved_at__range=(day_start, day_end)
        ).count())
        open_counts_weekly.append(Ticket.objects.filter(
            status='open',
            created_at__range=(day_start, day_end)
        ).count())
        closed_counts_weekly.append(Ticket.objects.filter(
            status='closed',
            closed_at__range=(day_start, day_end)
        ).count())
        pending_counts_weekly.append(Ticket.objects.filter(
            status='pending',
            created_at__range=(day_start, day_end)
        ).count())
    
    for month in reversed(range(9)):
        start_of_month = (today.replace(day=1) - timedelta(days=30 * month)).replace(day=1)
        end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
        
        resolved_counts_monthly.append(Ticket.objects.filter(
            status='resolved',
            resolved_at__range=[start_of_month, end_of_month]
        ).count())
        open_counts_monthly.append(Ticket.objects.filter(
            status='open',
            created_at__range=[start_of_month, end_of_month]
        ).count())
        closed_counts_monthly.append(Ticket.objects.filter(
            status='closed',
            closed_at__range=[start_of_month, end_of_month]
        ).count())
        pending_counts_monthly.append(Ticket.objects.filter(
            status='pending',
            created_at__range=[start_of_month, end_of_month]
        ).count())
    
    # else:
    #     support_member = SupportMember.objects.filter(user=request.user).first()
    #     if not support_member:
    #         return JsonResponse({"error": "No support member found for this user."})
        
    #     for day in last_seven_days:
    #         day_start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
    #         day_end = day_start + timedelta(days=1)  # The end of the day
            
    #         resolved_counts_weekly.append(Ticket.objects.filter(
    #             status='resolved',
    #             resolved_at__range=(day_start, day_end),
    #             assigned_to=support_member
    #         ).count())
    #         open_counts_weekly.append(Ticket.objects.filter(
    #             status='open',
    #             created_at__range=(day_start, day_end),
    #             assigned_to=support_member
    #         ).count())
    #         closed_counts_weekly.append(Ticket.objects.filter(
    #             status='closed',
    #             closed_at__range=(day_start, day_end),
    #             assigned_to=support_member
    #         ).count())
    #         pending_counts_weekly.append(Ticket.objects.filter(
    #             status='pending',
    #             created_at__range=(day_start, day_end),
    #             assigned_to=support_member
    #         ).count())
        
    #     for month in reversed(range(9)):
    #         start_of_month = (today.replace(day=1) - timedelta(days=30 * month)).replace(day=1)
    #         end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
            
    #         resolved_counts_monthly.append(Ticket.objects.filter(
    #             status='resolved',
    #             resolved_at__range=[start_of_month, end_of_month],
    #             assigned_to=support_member
    #         ).count())
    #         open_counts_monthly.append(Ticket.objects.filter(
    #             status='open',
    #             created_at__range=[start_of_month, end_of_month],
    #             assigned_to=support_member
    #         ).count())
    #         closed_counts_monthly.append(Ticket.objects.filter(
    #             status='closed',
    #             closed_at__range=[start_of_month, end_of_month],
    #             assigned_to=support_member
    #         ).count())
    #         pending_counts_monthly.append(Ticket.objects.filter(
    #             status='pending',
    #             created_at__range=[start_of_month, end_of_month],
    #             assigned_to=support_member
    #         ).count())
        
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
    tickets=Ticket.objects.filter(status=status).annotate(
        message_count=Count('messages'),
        attended_at=Subquery(
            TicketLog.objects.filter(
                ticket=OuterRef('pk'),
                status__icontains='pending'
            ).values('timestamp')[:1]
        )
    ).order_by('-created_at')
    # if request.user.is_superuser:
    #     tickets = Ticket.objects.filter(status=status)
    # else:
    #     support_member = SupportMember.objects.filter(user=request.user).first()
    #     if not support_member:
    #         return render(request, 'tickets/ticket_list.html', {'tickets': []})
    #     tickets = Ticket.objects.filter(status=status, assigned_to=support_member)
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
def profile_view(request):
    user = request.user
    return render(request, 'pages/profile.html', {'user': user})

@login_required
@staff_required
def support_users_list(request):
    support_members = SupportMember.objects.all()
    return render(request, 'pages/tables.html', {'support_members': support_members})

def branch_tickets(request, branch_name):
    tickets = Ticket.objects.filter(branch_opened__icontains=branch_name).annotate(
        message_count=Count('messages'),
        attended_at=Subquery(
            TicketLog.objects.filter(
                ticket=OuterRef('pk'),
                status__icontains='pending'
            ).values('timestamp')[:1]
        )
    ).order_by('-created_at')
    
    # if request.user.is_superuser:
    #     tickets = Ticket.objects.filter(branch_opened__icontains=branch_name).annotate(
    #         message_count=Count('messages'),
    #     ).order_by('-created_at')
    # else:
    #     support_member = SupportMember.objects.filter(user=request.user).first()
    #     if not support_member:
    #         return render(request, 'tickets/ticket_list.html', {'tickets': []})
    #     tickets = Ticket.objects.filter(branch_opened__icontains=branch_name, assigned_to=support_member).annotate(
    #         message_count=Count('messages'),
    #     ).order_by('-created_at')
    operator = request.GET.get('operator', '=')
    filter_time = request.GET.get('filter_time', None)
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
            pass  # Ig
    return render(request, 'tickets/ticket_list.html', {'tickets': tickets, 'branch': branch_name})

def escalated_tickets(request):
    escalated_subquery = TicketLog.objects.filter(
        ticket=OuterRef('pk'),
        changed_by__icontains='escalated'
    ).values('id')
    tickets = Ticket.objects.annotate(
        is_escalated=Exists(escalated_subquery),
        message_count=Count('messages'),
        attended_at=Subquery(
            TicketLog.objects.filter(
                ticket=OuterRef('pk'),
                status__icontains='pending'
            ).values('timestamp')[:1]
        )
    ).filter(is_escalated=True).order_by('-created_at')
    operator = request.GET.get('operator', '=')
    filter_time = request.GET.get('filter_time', None)
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
            pass  # Ig
    return render(request, 'tickets/ticket_list.html', {'tickets': tickets, 'escalated': True})

def creator_tickets(request, creator):
    creator = Ticket.objects.filter(id=creator).first().created_by
    tickets = Ticket.objects.filter(created_by=creator).annotate(
        message_count=Count('messages'),
        attended_at=Subquery(
            TicketLog.objects.filter(
                ticket=OuterRef('pk'),
                status__icontains='pending'
            ).values('timestamp')[:1]
        )
    ).order_by('-created_at')
    # if request.user.is_superuser:
    # else:
    #     support_member = SupportMember.objects.filter(user=request.user).first()
    #     if not support_member:
    #         return render(request, 'tickets/ticket_list.html', {'tickets': []})
    #     creator = Ticket.objects.filter(id=creator).first().created_by
    #     tickets = Ticket.objects.filter(created_by=creator, assigned_to=support_member).annotate(
    #         message_count=Count('messages'),
    #     ).order_by('-created_at')
    operator = request.GET.get('operator', '=')
    filter_time = request.GET.get('filter_time', None)
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
            pass  # Ig
    return render(request, 'tickets/ticket_list.html', {'tickets': tickets, 'creator': creator})

def support_member_tickets(request, member_id):

    member = SupportMember.objects.filter(id=member_id).first()
    # if request.user.is_superuser:
    # else:
    #     member = SupportMember.objects.filter(user=request.user).first()
    # if not member:
    #     return render(request, 'tickets/ticket_list.html', {'tickets': []})
    escalated_subquery = TicketLog.objects.filter(
        ticket=OuterRef('pk'),
        changed_by__icontains='escalated'
    ).values('id')

    tickets = Ticket.objects.filter(assigned_to=member.id).annotate(
        is_escalated=Exists(escalated_subquery),
        message_count=Count('messages'),
        attended_at=Subquery(
            TicketLog.objects.filter(
                ticket=OuterRef('pk'),
                status__icontains='pending'
            ).values('timestamp')[:1]
        )
    ).order_by('-created_at')
    
    for ticket in tickets:
        if ticket.status in ['resolved', 'closed']:
            if ticket.resolved_at:
                time_taken = ticket.resolved_at - ticket.created_at
            else:
                time_taken = ticket.closed_at - ticket.created_at
            ticket.time_taken = time_taken
        else:
            ticket.time_taken = None
    operator = request.GET.get('operator', '=')
    filter_time = request.GET.get('filter_time', None)
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
            pass  # Ig

    return render(request, 'tickets/ticket_list.html', {'tickets': tickets, 'member': member})

def all_tickets_list(request):
    operator = request.GET.get('operator', '=')
    filter_time = request.GET.get('filter_time', None)
    escalated_subquery = TicketLog.objects.filter(
        ticket=OuterRef('pk'),
        changed_by__icontains='escalated'
    ).values('id')
    tickets = Ticket.objects.order_by('-created_at').annotate(
            message_count=Count('messages'),
            is_escalated=Exists(escalated_subquery),
            attended_at=Subquery(
            TicketLog.objects.filter(
                ticket=OuterRef('pk'),
                status__icontains='pending'
            ).values('timestamp')[:1]
        )
    ).order_by('-created_at')
    # if request.user.is_superuser:
    # else:
    #     support_member = SupportMember.objects.filter(user=request.user).first()
    #     if not support_member:
    #         return render(request, 'tickets/ticket_list.html', {'tickets': []})
    #     escalated_subquery = TicketLog.objects.filter(
    #         ticket=OuterRef('pk'),
    #         changed_by__icontains='escalated'
    #     ).values('id')
    #     tickets = Ticket.objects.filter(assigned_to=support_member).order_by('-created_at').annotate(
    #             message_count=Count('messages'),
    #             is_escalated=Exists(escalated_subquery)
    #     ).order_by('-created_at')

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
    # if request.user.is_superuser:
    #     ticket = get_object_or_404(Ticket, id=ticket_id)
    # else:
    #     support_member = SupportMember.objects.filter(user=request.user).first()
    #     if not support_member:
    #         return HttpResponse("You are not authorized to view Inquiry!")
    #     ticket = get_object_or_404(Ticket, id=ticket_id, assigned_to=support_member)
    #     if not ticket:
    #         return HttpResponse("You are not authorized to view Inquiry!")
    messages = Message.objects.filter(ticket_id=ticket_id).order_by('created_at')
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

@api_view(['GET'])
def support_member_suggestions(request):
    members = SupportMember.objects.filter(is_active=True, is_deleted=False)
    serializer = SupportMemberSerializer(members, many=True)
    return Response(serializer.data)

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

