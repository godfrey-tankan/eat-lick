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

urlpatterns = [
    path('', include('home.urls')),
    path('admins/logout/', logout_view),
    path('tables/', support_users_list, name='support_users_list'),
    path('tickets/status/<str:status>/', ticket_list_by_status, name='ticket_list_by_status'),
    path('tickets/assigned-to/<int:member_id>/', support_member_tickets, name='tickets_by_assignee'),
    path('profile/', profile_view, name='profile'),
    path('edit/<int:id>/', edit_support_member, name='edit_support_member'),
    path("admins/", admin.site.urls),
    path("", include('admin_soft.urls')),
    path('webhook/', webhook, name='webhook'),
]
urlpatterns += [
    path('tickets/edit/<int:pk>/', TicketEditView.as_view(), name='ticket-edit'),
    path('tickets-create/', TicketListCreateView.as_view(), name='ticket-list-create'),
    path('tickets/<int:pk>/', TicketDetailView.as_view(), name='ticket-details'),

    path('ticket-logs/', TicketLogListCreateView.as_view(), name='ticketlog-list-create'),
    path('ticket-logs/<int:pk>/', TicketLogDetailView.as_view(), name='ticketlog-detail'),
    path('tickets/delete/<int:pk>/', TicketDeleteView.as_view(), name='ticket-delete'),

    path('comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),

    path('faqs/', FAQListCreateView.as_view(), name='faq-list-create'),
    path('faqs/<int:pk>/', FAQDetailView.as_view(), name='faq-detail'),
    path('tickets-list/', ticket_list, name='ticket-list'),
    path('tickets/create/', ticket_create, name='ticket-create'),
    path('ticket/<int:pk>/', ticket_detail, name='ticket-detail'),
    path('get-chart-data/', get_chart_data, name='get_chart_data'),
    path('weekly-report/', weekly_report_pdf, name='weekly_report_pdf'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)