from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    CustomAuthToken, custom_login, custom_logout,
    UserViewSet, InquirerViewSet, SupportMemberViewSet,
    BranchViewSet, TicketViewSet, TicketLogViewSet,
    CommentViewSet, FAQViewSet, MessageViewSet,
    dashboard_stats, chart_data, support_member_suggestions,
    create_ticket, handle_branches
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'inquirers', InquirerViewSet)
router.register(r'support-members', SupportMemberViewSet)
router.register(r'branches', BranchViewSet)
router.register(r'tickets', TicketViewSet)
router.register(r'ticket-logs', TicketLogViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'faqs', FAQViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    # Authentication
    path('auth/login/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('auth/custom-login/', custom_login, name='custom_login'),
    path('auth/logout/', custom_logout, name='custom_logout'),
        
    # Dashboard and reports
    path('dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    path('dashboard/chart-data/', chart_data, name='chart_data'),
    
    # Additional endpoints
    path('support-member-suggestions/', support_member_suggestions, name='support_member_suggestions'),
    path('create-ticket/', create_ticket, name='create_ticket'),
    path('branches/', handle_branches, name='handle_branches'),
    
    # Include all router URLs
    path('', include(router.urls)),
]