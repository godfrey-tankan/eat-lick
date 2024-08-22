"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from home.views import *
from a_bot.webhooks import webhook
from a_bot.accept_ticket import *
from django.conf import settings
from django.conf.urls.static import static
from a_bot.logout import logout_view
from home.report import *
from home.global_search import global_search
from home.escalate_ticket import escalate_ticket, send_message
from home.fetch_messages import fetch_messages
from a_bot.views import forward_message
from home.web_support import web_support
from home.web_reports import *

urlpatterns = [
    path('', include('home.urls')),
    path('admins/logout/', logout_view),
    path('tables/', support_users_list, name='support_users_list'),
    
    path('users/', users_list, name='user_list'),
    path('user/<int:id>/', edit_user, name='edit_user'),
    path('profile/', profile_view, name='profile'),
    path('edit/<int:id>/', edit_support_member, name='edit_support_member'),
    path("admins/", admin.site.urls),
    path("", include('admin_soft.urls')),
    path('webhook/', webhook, name='webhook'),
    path('search/', global_search, name='global_search'),
    path('escalate/<int:ticket_id>/', escalate_ticket, name='escalate_ticket'),
    path('send-message/<int:ticket_id>/', send_message, name='send_message'),
    path('get/support-members/', support_member_suggestions, name='support_member_suggestions'),
    # PDF REPORTS
    path('generate_support_member_report/', generate_support_member_report, name='generate_support_member_report'),
    path('generate_branch_report/', generate_branch_report, name='generate_branch_report'),
    path('generate_weekly_report/', generate_weekly_report, name='generate_weekly_report'),
    path('generate_overall_report/', generate_overall_report, name='generate_overall_report'),
    path('generate_monthly_report/', generate_monthly_report, name='generate_monthly_report'),
    # WEB REPORTS
    path('reports/weekly/', weekly_report_page, name='weekly_report_page'),
    path('reports/monthly/', monthly_report_view, name='monthly_report'),
    path('reports/support_member/', support_member_report_view, name='support_member_report'),
    path('reports/overall/', overall_report_view, name='overall_report'),
    path('reports/branch/', branch_report_view, name='branch_report'),
    
    path('web-support/', web_support, name='web_support'),
    path('web-support/chat/', web_support, name='web_support'),
]
urlpatterns += [
    path('tickets/edit/<int:pk>/', TicketEditView.as_view(), name='ticket-edit'),
    path('tickets-create/', TicketListCreateView.as_view(), name='ticket-list-create'),
    path('tickets/<int:pk>/', TicketDetailView.as_view(), name='ticket-details'),

    path('ticket-logs/', TicketLogListCreateView.as_view(), name='ticketlog-list-create'),
    path('ticket-logs/<int:pk>/', TicketLogDetailView.as_view(), name='ticketlog-detail'),
    path('tickets/delete/<int:pk>/', TicketDeleteView.as_view(), name='ticket-delete'),
    path('ticket/<int:ticket_id>/', ticket_detail_view, name='ticket_detail'),
    path('ticket/<int:ticket_id>/fetch-messages/', fetch_messages, name='fetch_messages'),
    path('send-img/', forward_message, name='forward_message'),

    path('comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),

    path('faqs/', FAQListCreateView.as_view(), name='faq-list-create'),
    path('faqs/<int:pk>/', FAQDetailView.as_view(), name='faq-detail'),
    path('tickets/create/', ticket_create, name='ticket-create'),
    path('ticket/<int:pk>/', ticket_detail, name='ticket-detail'),
    path('get-chart-data/', get_chart_data, name='get_chart_data'),
    # path('reports/weekly/', generate_weekly_report, name='generate_weekly_report'),
    path('inquiries/', all_tickets_list, name='inquiries_list'),
    path('tickets/status/<str:status>/', ticket_list_by_status, name='ticket_list_by_status'),
    path('tickets/assigned-to/<int:member_id>/', support_member_tickets, name='tickets_by_assignee'),
    path('tickets/branch/<str:branch_name>/', branch_tickets, name='tickets_by_branch'),
    path('tickets/escalated/', escalated_tickets, name='escalated_tickets'),
    path('tickets/creator/<str:creator>/', creator_tickets, name='tickets_by_creator'),
]
all_tickets_list
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)