from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.db.models import Count, Q, Exists, OuterRef, Subquery, FloatField, ExpressionWrapper, F, Avg
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
    DashboardStatsSerializer, ChartDataSerializer
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

# Add other endpoints as needed