from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.db.models import Count, Q, Exists, OuterRef, Subquery, FloatField, ExpressionWrapper, F, Avg, DurationField
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from home.models import (
    Inquirer, SupportMember, Ticket, TicketLog, 
    Comment, FAQ, Message, Branch
)
from .serializers import (
    UserSerializer, UserCreateSerializer, InquirerSerializer, 
    SupportMemberSerializer, BranchSerializer, TicketSerializer, 
    TicketLogSerializer, CommentSerializer, FAQSerializer, 
    MessageSerializer, SupportMemberStatsSerializer, 
    DashboardStatsSerializer, ChartDataSerializer,
    ReportSerializer
)
from home.views import get_support_members_stats, get_chart_data
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()

# Authentication Views
class CustomAuthToken(ObtainAuthToken):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        # Serialize user data
        user_serializer = UserSerializer(user)
        
        return Response({
            'token': token.key,
            'user': user_serializer.data
        })

@csrf_exempt  # You can remove this if you enable CSRF in frontend or use @api_view (recommended)
@api_view(['POST'])
@permission_classes([AllowAny])
def custom_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)  # Optional: logs in via Django session
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'status': 'success',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                # Add more fields if needed
            }
        }, status=status.HTTP_200_OK)

    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def custom_logout(request):
    logout(request)
    return Response({"detail": "Successfully logged out."})

# Model Viewsets
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class InquirerViewSet(viewsets.ModelViewSet):
    queryset = Inquirer.objects.all()
    serializer_class = InquirerSerializer
    permission_classes = [permissions.IsAuthenticated]

class SupportMemberViewSet(viewsets.ModelViewSet):
    queryset = SupportMember.objects.all()
    serializer_class = SupportMemberSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination for stats action
    @action(detail=False, methods=['get'])
    def stats(self, request):
        support_members = get_support_members_stats(request)
        # Convert to serializable format
        data = []
        for member in support_members:
            data.append({
                'id': member.id,
                'username': member.username,
                'total_resolved': member.total_resolved,
                'total_closed_tickets': member.total_closed_tickets,
                'total_pending_tickets': member.total_pending_tickets,
                'total_assigned_tickets': member.total_assigned_tickets,
                'average_rating': float(member.average_rating) if member.average_rating else 0.0,
                'percentage_resolved': float(member.percentage_resolved) if member.percentage_resolved else 0.0,
                'percentage_closed': float(member.percentage_closed) if member.percentage_closed else 0.0,
                'percentage_pending': float(member.percentage_pending) if member.percentage_pending else 0.0,
                'percentage_expired': float(member.percentage_expired) if member.percentage_expired else 0.0,
            })
        return Response(data)

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Ticket.objects.all()
        
        # Apply filters based on query parameters
        status = self.request.query_params.get('status', None)
        branch = self.request.query_params.get('branch', None)
        creator = self.request.query_params.get('creator', None)
        member_id = self.request.query_params.get('member_id', None)
        escalated = self.request.query_params.get('escalated', None)
        
        if status:
            queryset = queryset.filter(status=status)
        if branch:
            queryset = queryset.filter(branch_opened__icontains=branch)
        if creator:
            queryset = queryset.filter(created_by__id=creator)
        if member_id:
            queryset = queryset.filter(assigned_to__id=member_id)
        if escalated and escalated.lower() == 'true':
            escalated_subquery = TicketLog.objects.filter(
                ticket=OuterRef('pk'),
                changed_by__icontains='escalated'
            ).values('id')
            queryset = queryset.annotate(
                is_escalated=Exists(escalated_subquery)
            ).filter(is_escalated=True)
        
        # Add annotations for additional data
        escalated_subquery = TicketLog.objects.filter(
            ticket=OuterRef('pk'),
            changed_by__icontains='escalated'
        ).values('id')
        
        queryset = queryset.annotate(
            message_count=Count('messages'),
            is_escalated=Exists(escalated_subquery),
            attended_at=Subquery(
                TicketLog.objects.filter(
                    ticket=OuterRef('pk'),
                    status__icontains='pending'
                ).values('timestamp')[:1]
            )
        ).order_by('-created_at')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def escalate(self, request, pk=None):
        ticket = self.get_object()
        # Your escalate logic here
        return Response({"detail": "Ticket escalated successfully."})
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        ticket = self.get_object()
        # Your send message logic here
        return Response({"detail": "Message sent successfully."})

class TicketLogViewSet(viewsets.ModelViewSet):
    queryset = TicketLog.objects.all()
    serializer_class = TicketLogSerializer
    permission_classes = [permissions.IsAuthenticated]

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [permissions.IsAuthenticated]

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

# Dashboard and Report Views
# Add these imports at the top
from django.utils.timezone import make_aware, now
from django.http import JsonResponse
import json
from datetime import timedelta, datetime

# Update the dashboard_stats function
@api_view(['GET'])
def dashboard_stats(request):
    # Get all tickets
    all_tickets = Ticket.objects.all()
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
    ).count()
    
    def calculate_percentage(count):
        return round((count / total_tickets * 100), 2) if total_tickets > 0 else 0
    
    # Get support member stats
    support_members_stats = get_support_members_stats(request)
    
    data = {
        "tickets_count": total_tickets,
        "open_tickets_count": open_tickets_count,
        "closed_tickets_count": closed_tickets_count,
        "pending_tickets_count": pending_tickets_count,
        "resolved_tickets_count": resolved_tickets_count,
        "open_tickets_percentage": calculate_percentage(open_tickets_count),
        "closed_tickets_percentage": calculate_percentage(closed_tickets_count),
        "pending_tickets_percentage": calculate_percentage(pending_tickets_count),
        "resolved_tickets_percentage": calculate_percentage(resolved_tickets_count),
        "active_support_members": active_support_members,
        "sp": support_members_stats
    }
    
    # Convert QuerySet to list of dicts for serialization
    sp_data = []
    for member in support_members_stats:
        sp_data.append({
            "id": member.id,
            "username": member.username,
            "total_resolved": member.total_resolved,
            "total_closed_tickets": member.total_closed_tickets,
            "total_pending_tickets": member.total_pending_tickets,
            "total_assigned_tickets": member.total_assigned_tickets,
            "average_rating": float(member.average_rating) if member.average_rating else 0.0,
            "percentage_resolved": float(member.percentage_resolved) if member.percentage_resolved else 0.0,
            "percentage_closed": float(member.percentage_closed) if member.percentage_closed else 0.0,
            "percentage_pending": float(member.percentage_pending) if member.percentage_pending else 0.0,
            "percentage_expired": float(member.percentage_expired) if member.percentage_expired else 0.0,
        })
    
    data["sp"] = sp_data
    
    return Response(data)

# Update the chart_data function
@api_view(['GET'])
def chart_data(request):
    today = now()  
    start_of_week = today - timedelta(days=today.weekday())
    last_seven_days = [start_of_week + timedelta(days=i) for i in range(7)]
    last_nine_months = [(today - timedelta(days=30 * i)).strftime('%b') for i in reversed(range(9))]
    
    resolved_counts_weekly = []
    open_counts_weekly = []
    closed_counts_weekly = []
    pending_counts_weekly = []
    resolved_counts_monthly = []
    open_counts_monthly = []
    closed_counts_monthly = []
    pending_counts_monthly = []
    
    for day in last_seven_days:
        day_start = make_aware(datetime.combine(day, datetime.min.time()))
        day_end = day_start + timedelta(days=1) 
        
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
    
    return Response(data)
# Additional endpoints from your home.urls
@api_view(['GET'])
def support_member_suggestions(request):
    members = SupportMember.objects.filter(is_active=True, is_deleted=False)
    serializer = SupportMemberSerializer(members, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create_ticket(request):
    # Your create ticket logic here
    pass

@api_view(['GET', 'POST'])
def handle_branches(request, branch_id=None):
    if request.method == 'GET':
        branches = Branch.objects.all()
        serializer = BranchSerializer(branches, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = BranchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReportViewSet(viewsets.ViewSet):
    """
    ViewSet for generating various reports
    """
    pagination_class = None
    
    def _get_date_range(self, time_range):
        """Helper method to get date range based on time period"""
        today = now().date()
        
        if time_range == 'last_7_days':
            start_date = today - timedelta(days=7)
        elif time_range == 'last_30_days':
            start_date = today - timedelta(days=30)
        elif time_range == 'this_month':
            start_date = today.replace(day=1)
        elif time_range == 'last_month':
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            start_date = last_day_last_month.replace(day=1)
            end_date = last_day_last_month
            return start_date, end_date
        elif time_range == 'this_quarter':
            current_month = today.month
            current_quarter = (current_month - 1) // 3 + 1
            start_date = today.replace(month=3*(current_quarter-1)+1, day=1)
        elif time_range == 'last_quarter':
            current_month = today.month
            current_quarter = (current_month - 1) // 3 + 1
            if current_quarter == 1:
                start_date = today.replace(year=today.year-1, month=10, day=1)
                end_date = today.replace(year=today.year-1, month=12, day=31)
            else:
                start_date = today.replace(month=3*(current_quarter-2)+1, day=1)
                end_date = today.replace(month=3*(current_quarter-1), day=1) - timedelta(days=1)
            return start_date, end_date
        elif time_range == 'this_year':
            start_date = today.replace(month=1, day=1)
        else:
            # Default to last 7 days
            start_date = today - timedelta(days=7)
        
        return start_date, today

    @action(detail=False, methods=['post'])
    def weekly(self, request):
        """Generate weekly report"""
        return self._generate_report(request, 'weekly')

    @action(detail=False, methods=['post'])
    def monthly(self, request):
        """Generate monthly report"""
        return self._generate_report(request, 'monthly')

    @action(detail=False, methods=['post'],pagination_class=None)
    def support_member(self, request):
        """Generate support member report"""
        return self._generate_report(request, 'support_member')

    @action(detail=False, methods=['post'])
    def branch(self, request):
        """Generate branch report"""
        return self._generate_report(request, 'branch')

    @action(detail=False, methods=['post'])
    def overall(self, request):
        """Generate overall report"""
        return self._generate_report(request, 'overall')

    def _generate_report(self, request, report_type):
        """Generate reports based on type and filters"""
        # Get filters from request
        time_range = request.data.get('time_range', 'last_7_days')
        branch_id = request.data.get('branch_id')
        support_member_id = request.data.get('support_member_id')

        # Get date range
        start_date, end_date = self._get_date_range(time_range)

        # Base queryset
        tickets = Ticket.objects.filter(
            created_at__date__range=[start_date, end_date]
        )
        # Apply additional filters
        if branch_id:
            if branch := Branch.objects.filter(id=branch_id).first():
                tickets = tickets.filter(Q(branch_opened__icontains=branch) | Q(branch_opened__icontains=branch.code))

        if support_member_id:
            tickets = tickets.filter(assigned_to_id=support_member_id)

        if report_type == 'weekly':
            data = self._generate_weekly_report(tickets, start_date, end_date)
        elif report_type == 'monthly':
            data = self._generate_monthly_report(tickets, start_date, end_date)
        elif report_type == 'support_member':
            data = self._generate_support_member_report(tickets, start_date, end_date)
        elif report_type == 'branch':
            data = self._generate_branch_report(tickets)
        elif report_type == 'overall':
            data = self._generate_overall_report(tickets)
        else:
            return Response(
                {'error': 'Invalid report type'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add metadata
        data['metadata'] = {
            'report_type': report_type,
            'time_range': time_range,
            'start_date': start_date,
            'end_date': end_date,
            'generated_at': now(),
        }

        serializer = ReportSerializer(data)
        return Response(serializer.data)

    def _generate_weekly_report(self, tickets, start_date, end_date):
        """Generate weekly report data"""
        # Group tickets by day
        daily_stats = []
        current_date = start_date
        while current_date <= end_date:
            day_tickets = tickets.filter(created_at__date=current_date)
            daily_stats.append({
                'date': current_date,
                'total_tickets': day_tickets.count(),
                'resolved_tickets': day_tickets.filter(status='resolved').count(),
                'open_tickets': day_tickets.filter(status='open').count(),
                'pending_tickets': day_tickets.filter(status='pending').count(),
                'closed_tickets': day_tickets.filter(status='closed').count(),
            })
            current_date += timedelta(days=1)
        
        # Calculate overall stats
        total_tickets = tickets.count()
        resolved_tickets = tickets.filter(status='resolved').count()
        
        return {
            'daily_stats': daily_stats,
            'total_tickets': total_tickets,
            'resolved_tickets': resolved_tickets,
            'resolution_rate': (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0,
            'average_resolution_time': self._get_average_resolution_time(tickets),
        }

    def _generate_monthly_report(self, tickets, start_date, end_date):
        """Generate monthly report data"""
        # Similar to weekly but grouped by week
        weekly_stats = []
        current_date = start_date
        while current_date <= end_date:
            week_end = min(current_date + timedelta(days=6), end_date)
            week_tickets = tickets.filter(created_at__date__range=[current_date, week_end])
            
            weekly_stats.append({
                'week_start': current_date,
                'week_end': week_end,
                'total_tickets': week_tickets.count(),
                'resolved_tickets': week_tickets.filter(status='resolved').count(),
            })
            
            current_date = week_end + timedelta(days=1)
        
        return {
            'weekly_stats': weekly_stats,
            'total_tickets': tickets.count(),
            'resolved_tickets': tickets.filter(status='resolved').count(),
            'average_resolution_time': self._get_average_resolution_time(tickets),
        }

    def _generate_support_member_report(self, tickets, start_date, end_date):
        """Generate support member performance report"""
        support_members = SupportMember.objects.all()
        member_stats = []
        
        for member in support_members:
            member_tickets = tickets.filter(assigned_to=member)
            resolved_tickets = member_tickets.filter(status='resolved')
            
            member_stats.append({
                'id': member.id,
                'username': member.username,
                'total_tickets': member_tickets.count(),
                'resolved_tickets': resolved_tickets.count(),
                'resolution_rate': (resolved_tickets.count() / member_tickets.count() * 100) if member_tickets.count() > 0 else 0,
                'average_rating': resolved_tickets.aggregate(Avg('support_level'))['support_level__avg'] or 0,
                'average_resolution_time': self._get_average_resolution_time(member_tickets),
            })
        
        return {
            'support_member_stats': sorted(member_stats, key=lambda x: x['resolved_tickets'], reverse=True),
            'time_period': f"{start_date} to {end_date}",
        }

    def _generate_branch_report(self, tickets):
        """Generate branch performance report"""
        branches = Branch.objects.all()
        branch_stats = []
        
        for branch in branches:
            branch_tickets = tickets.filter(branch_opened=branch.name)
            resolved_tickets = branch_tickets.filter(status='resolved')
            
            branch_stats.append({
                'id': branch.id,
                'name': branch.name,
                'code': branch.code,
                'total_tickets': branch_tickets.count(),
                'resolved_tickets': resolved_tickets.count(),
                'resolution_rate': (resolved_tickets.count() / branch_tickets.count() * 100) if branch_tickets.count() > 0 else 0,
                'average_resolution_time': self._get_average_resolution_time(branch_tickets),
            })
        
        return {
            'branch_stats': sorted(branch_stats, key=lambda x: x['total_tickets'], reverse=True),
        }

    def _generate_overall_report(self, tickets):
        """Generate overall system report"""
        total_tickets = tickets.count()
        resolved_tickets = tickets.filter(status='resolved').count()
        
        # Ticket status distribution
        status_distribution = {
            'open': tickets.filter(status='open').count(),
            'pending': tickets.filter(status='pending').count(),
            'resolved': resolved_tickets,
            'closed': tickets.filter(status='closed').count(),
            'expired': tickets.filter(status='expired').count(),
        }
        
        # Resolution time analysis
        resolution_times = self._get_resolution_time_analysis(tickets)
        return {
            'total_tickets': total_tickets,
            'resolved_tickets': resolved_tickets,
            'resolution_rate': (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0,
            'status_distribution': status_distribution,
            'average_resolution_time': self._get_average_resolution_time(tickets),
            'resolution_time_analysis': resolution_times,
            'busiest_day': self._get_busiest_day(tickets),
            'top_performers': self._get_top_performers(tickets),
        }

    def _get_average_resolution_time(self, tickets):
        resolved_tickets = tickets.filter(status='resolved')
        if not resolved_tickets.exists():
            return 0

        avg_seconds = resolved_tickets.annotate(
            resolution_time=ExpressionWrapper(
                F('resolved_at') - F('created_at'),
                output_field=DurationField()
            )
        ).aggregate(Avg('resolution_time'))['resolution_time__avg']

        hours = avg_seconds.total_seconds() / 3600 if avg_seconds else 0
        return max(hours, 0) 

    def _get_resolution_time_analysis(self, tickets):
        """Analyze resolution time distribution"""
        resolved_tickets = tickets.filter(status='resolved').annotate(
            resolution_time=ExpressionWrapper(
                F('resolved_at') - F('created_at'),
                output_field=DurationField()
            )
        )
        
        # Categorize by resolution time
        categories = {
            'under_1_hour': resolved_tickets.filter(resolution_time__lt=timedelta(hours=1)).count(),
            '1_4_hours': resolved_tickets.filter(
                resolution_time__gte=timedelta(hours=1),
                resolution_time__lt=timedelta(hours=4)
            ).count(),
            '4_24_hours': resolved_tickets.filter(
                resolution_time__gte=timedelta(hours=4),
                resolution_time__lt=timedelta(hours=24)
            ).count(),
            '1_3_days': resolved_tickets.filter(
                resolution_time__gte=timedelta(days=1),
                resolution_time__lt=timedelta(days=3)
            ).count(),
            'over_3_days': resolved_tickets.filter(resolution_time__gte=timedelta(days=3)).count(),
        }
        
        return categories

    def _get_busiest_day(self, tickets):
        """Find the busiest day for ticket creation"""
        from django.db.models.functions import TruncDay
        
        daily_counts = tickets.annotate(day=TruncDay('created_at')).values('day').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return daily_counts.first() if daily_counts else None

    def _get_top_performers(self, tickets, limit=5):
        support_members = SupportMember.objects.annotate(
            resolved_count=Count('assigned_tickets', filter=Q(assigned_tickets__status='resolved')),
            avg_resolution_time=Avg(
                ExpressionWrapper(
                    F('assigned_tickets__resolved_at') - F('assigned_tickets__created_at'),
                    output_field=DurationField()
                ),
                filter=Q(assigned_tickets__status='resolved')
            )
        ).filter(resolved_count__gt=0).order_by('-resolved_count')[:limit]

        return [
            {
                'id': member.id,
                'username': member.username,
                'resolved_tickets': member.resolved_count,
                'average_resolution_time': member.avg_resolution_time.total_seconds() / 3600 if member.avg_resolution_time else 0,
            }
            for member in support_members
        ]

    
    @action(detail=False, methods=['post'])
    def ai_summarized(self, request):
        from .helpers import summarize_with_gemini
        """Generate AI-summarized report using Gemini"""
        report_type = request.data.get('report_type','overall')
        if not report_type:
            return Response({'error': 'report_type is required'}, status=400)
        
        # Use same logic as _generate_report to get tickets
        time_range = request.data.get('time_range', 'last_7_days')
        branch_id = request.data.get('branch_id')
        support_member_id = request.data.get('support_member_id')

        start_date, end_date = self._get_date_range(time_range)
        tickets = Ticket.objects.filter(created_at__date__range=[start_date, end_date])

        if branch_id:
            if branch := Branch.objects.filter(id=branch_id).first():
                tickets = tickets.filter(Q(branch_opened__icontains=branch) | Q(branch_opened__icontains=branch.code))

        if support_member_id:
            tickets = tickets.filter(assigned_to_id=support_member_id)

        # Reuse report generation methods
        if report_type == 'weekly':
            report_data = self._generate_weekly_report(tickets, start_date, end_date)
        elif report_type == 'monthly':
            report_data = self._generate_monthly_report(tickets, start_date, end_date)
        elif report_type == 'support_member':
            report_data = self._generate_support_member_report(tickets, start_date, end_date)
        elif report_type == 'branch':
            report_data = self._generate_branch_report(tickets)
        elif report_type == 'overall':
            report_data = self._generate_overall_report(tickets)
        else:
            return Response({'error': 'Invalid report type'}, status=400)

        # Summarize using Gemini
        summary = summarize_with_gemini(report_data, report_type)

        return Response({
            'summary': summary,
            'metadata': {
                'report_type': report_type,
                'time_range': time_range,
                'start_date': start_date,
                'end_date': end_date,
            }
        })