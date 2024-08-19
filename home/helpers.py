from datetime import datetime, timedelta
from django.utils.timezone import now
import re
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import timedelta,datetime
from django.utils.timezone import now
from .models import Ticket, SupportMember, Inquirer, Branch, TicketLog
from django.db.models import Count, Q,OuterRef,Exists,Avg,FloatField
from django.db.models.functions import Cast
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt





def prepare_branch_report_context(branch, tickets, start_date, end_date):
    branch_stats = tickets.values('branch_opened').annotate(
        open_count=Count('id', filter=Q(status='open')),
        pending_count=Count('id', filter=Q(status='pending')),
        closed_count=Count('id', filter=Q(status='closed')),
        resolved_count=Count('id', filter=Q(status='resolved'))
    )
    
    total_opened = tickets.filter(status='open').count()
    total_closed = tickets.filter(status='closed').count()
    total_resolved = tickets.filter(status='resolved').count()
    total_pending = tickets.filter(status='pending').count()
    
    daily_counts = tickets.values('created_at__date').annotate(
        opened=Count('id', filter=Q(status='open')),
        closed=Count('id', filter=Q(status='closed')),
        resolved=Count('id', filter=Q(status='resolved')),
        pending_tickets=Count('id', filter=Q(status='pending'))
    ).order_by('created_at__date')
    
    day_most_opened = daily_counts.order_by('-opened').first()
    day_most_closed = daily_counts.order_by('-closed').first()
    day_most_resolved = daily_counts.order_by('-resolved').first()
    day_most_pending = daily_counts.order_by('-pending_tickets').first()

    return {
        'branch': branch,
        'branch_stats': branch_stats,
        'total_opened': total_opened,
        'total_closed': total_closed,
        'total_resolved': total_resolved,
        'total_pending': total_pending,
        'daily_counts': daily_counts,
        'day_most_opened': day_most_opened,
        'day_most_closed': day_most_closed,
        'day_most_pending': day_most_pending,
        'day_most_resolved': day_most_resolved,
        'start_date': start_date,
        'end_date': end_date,
    }
    
def prepare_empty_branch_report_context(branch, start_date, end_date):
    return {
        'branch': branch,
        'branch_stats': [],
        'total_opened': 0,
        'total_closed': 0,
        'total_resolved': 0,
        'total_pending': 0,
        'daily_counts': [],
        'day_most_opened': [],
        'day_most_closed': [],
        'day_most_pending': [],
        'day_most_resolved': [],
        'start_date': start_date,
        'end_date': end_date,
    }
    
def prepare_overall_report_context(tickets, start_date, end_date):
    support_members = SupportMember.objects.all()
    branch_stats = tickets.values('branch_opened').annotate(
        total_tickets=Count('id'),
        open_count=Count('id', filter=Q(status='open')),
        pending_count=Count('id', filter=Q(status='pending')),
        closed_count=Count('id', filter=Q(status='closed')),
        resolved_count=Count('id', filter=Q(status='resolved'))
    ).order_by('-total_tickets')
    branch_most_inquiries = branch_stats.first()
    total_inquiries = Ticket.objects.count()
    
    open_tickets_filter = tickets.filter(status='open')
    pending_tickets_filter = tickets.filter(status='pending')
    closed_tickets_filter = tickets.filter(status='closed')
    resolved_tickets_filter = tickets.filter(status='resolved')
    
    
    total_resolved = resolved_tickets_filter.count()
    total_closed = closed_tickets_filter.count()
    total_pending = pending_tickets_filter.count()
    total_open = open_tickets_filter.count()
    

    report_data = []
    for member in support_members:
        tickets_for_member = tickets.filter(assigned_to=member.id)
        resolved_tickets = tickets_for_member.filter(status='resolved')
        closed_tickets = tickets_for_member.filter(status='closed')
        pending_tickets = tickets_for_member.filter(status='pending')
        total_time = timedelta()
        resolved_ticket_count = 0
        
        for ticket in resolved_tickets:
            if ticket.resolved_at:
                total_time += ticket.resolved_at - ticket.created_at
                resolved_ticket_count += 1
        
        average_time_hours = (total_time.total_seconds() / 3600) / resolved_ticket_count if resolved_ticket_count > 0 else 0
        average_time = f"{average_time_hours:.2f} hours"
        
        report_data.append({
            'member': member.username,
            'total_resolved_count': resolved_ticket_count,
            'pending_tickets_count': pending_tickets,
            'total_closed_count': closed_tickets,
            'average_time': average_time
        })

    return {
        'branch_stats': branch_stats,
        'branch_most_inquiries': branch_most_inquiries,
        'total_inquiries': total_inquiries,
        'total_open': total_open,
        'total_pending': total_pending,
        'total_closed': total_closed,
        'total_resolved': total_resolved,
        
        'report_data': report_data,
        'start_date': start_date,
        'end_date': end_date,
    }

def prepare_empty_overall_report_context(start_date, end_date):
    return {
        'branch_stats': [],
        'branch_most_inquiries': None,
        'total_inquiries': 0,
        'report_data': [],
        'start_date': start_date,
        'end_date': end_date,
    }
    
def prepare_support_member_report_context(member, tickets, start_date, end_date):
    resolved_tickets = tickets.filter(status='resolved')
    closed_tickets = tickets.filter(status='closed')
    pending_tickets = tickets.filter(status='pending')

    total_resolved_count = resolved_tickets.count()
    total_closed_count = closed_tickets.count()
    pending_tickets_count = pending_tickets.count()
    
    total_time = timedelta()
    resolved_ticket_count = 0
    
    for ticket in resolved_tickets:
        if ticket.resolved_at:
            total_time += ticket.resolved_at - ticket.created_at
            resolved_ticket_count += 1
    
    average_time_hours = (total_time.total_seconds() / 3600) / resolved_ticket_count if resolved_ticket_count > 0 else 0
    average_time = f"{average_time_hours:.2f} hours"

    return {
        'member': member,
        'resolved_count': total_resolved_count,
        'pending_count': pending_tickets_count,
        'closed_count': total_closed_count,
        'average_time': average_time,
        'start_date': start_date,
        'end_date': end_date,
    }
    
def prepare_empty_support_member_report_context(member, start_date, end_date):
    return {
        'member': member,
        'resolved_count': 0,
        'pending_count': 0,
        'closed_count': 0,
        'average_time': "N/A",
        'start_date': start_date,
        'end_date': end_date,
    }
    
def prepare_monthly_report_context(tickets, start_date, end_date):
    support_members = SupportMember.objects.all()
    branch_stats = tickets.values('branch_opened').annotate(tickets=Count('id')).order_by('-tickets')
    ticket_counts = tickets.values('branch_opened').annotate(
        open_count=Count('id', filter=Q(status='open')),
        pending_count=Count('id', filter=Q(status='pending')),
        closed_count=Count('id', filter=Q(status='closed')),
        resolved_count=Count('id', filter=Q(status='resolved'))
    )
    branch_most_inquiries = branch_stats.first()
    total_inquiries = branch_stats.aggregate(total=Count('id'))['total']

    total_opened = tickets.filter(status='open').count()
    total_closed = tickets.filter(status='closed').count()
    total_resolved = tickets.filter(status='resolved').count()
    total_pending = tickets.filter(status='pending').count()

    daily_counts = tickets.values('created_at__date').annotate(
        opened=Count('id', filter=Q(status='open')),
        closed=Count('id', filter=Q(status='closed')),
        resolved=Count('id', filter=Q(status='resolved')),
        pending_tickets=Count('id', filter=Q(status='pending'))
    ).order_by('created_at__date')

    day_most_opened = daily_counts.order_by('-opened').first()
    day_most_closed = daily_counts.order_by('-closed').first()
    day_most_resolved = daily_counts.order_by('-resolved').first()
    day_most_pending = daily_counts.order_by('-pending_tickets').first()

    report_data = []
    for member in support_members:
        tickets_for_member = tickets.filter(assigned_to=member.id)
        resolved_tickets = tickets_for_member.filter(status='resolved')
        closed_tickets = tickets_for_member.filter(status='closed')
        pending_tickets = tickets_for_member.filter(status='pending')

        total_resolved_count = resolved_tickets.count()
        total_closed_count = closed_tickets.count()
        pending_tickets_count = pending_tickets.count()

        total_time = timedelta()
        resolved_ticket_count = 0

        for ticket in resolved_tickets:
            if ticket.resolved_at:
                total_time += ticket.resolved_at - ticket.created_at
                resolved_ticket_count += 1

        average_time_hours = (total_time.total_seconds() / 3600) / resolved_ticket_count if resolved_ticket_count > 0 else 0
        average_time = f"{average_time_hours:.2f} hours"

        report_data.append({
            'member': member.username,
            'resolved_count': total_resolved_count,
            'pending_count': pending_tickets_count,
            'closed_count': total_closed_count,
            'average_time': average_time
        })

    return {
        'branch_stats': branch_stats,
        'ticket_counts': ticket_counts,
        'branch_most_inquiries': branch_most_inquiries,
        'total_inquiries': total_inquiries,
        'report_data': report_data,
        'start_date': datetime.strftime(start_date, '%d %B %Y'),
        'end_date': datetime.strftime(end_date, '%d %B %Y'),
        'total_opened': total_opened,
        'total_pending': total_pending,
        'total_closed': total_closed,
        'total_resolved': total_resolved,
        'daily_counts': daily_counts,
        'day_most_opened': day_most_opened,
        'day_most_closed': day_most_closed,
        'day_most_pending': day_most_pending,
        'day_most_resolved': day_most_resolved,
    }

def prepare_empty_monthly_report_context(start_date, end_date):
    context = {
        'branch_stats': [],
        'ticket_counts': [],
        'branch_most_inquiries': [],
        'total_inquiries': 0,
        'report_data': [],
        'start_date': start_date,
        'end_date': end_date,
        'total_opened': 0,
        'total_pending': 0,
        'total_closed': 0,
        'total_resolved': 0,
        'daily_counts': [],
        'day_most_opened': [],
        'day_most_closed': [],
        'day_most_pending': [],
        'day_most_resolved': [],
    }
    
    return context

def get_current_month_dates(today=None):
    if today:
        try:
            today = datetime.strptime(today, '%Y-%m-%d').date()
        except ValueError:
            print('Invalid date format, using current date')
            today = datetime.now().date()
    else:
        today = datetime.now().date()
    year = today.year
    month = today.month
    start_date = datetime(year, month, 1).date()

    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

    return start_date, end_date

def format_phone_number(phone_number):
    match = re.search(r'7', phone_number)
    if match:
        formatted_number = '263' + phone_number[match.start():]
        return formatted_number
    else:
        return phone_number