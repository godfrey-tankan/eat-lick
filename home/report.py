from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import timedelta,datetime
from django.utils.timezone import now
from .models import Ticket, SupportMember, Inquirer, Branch
from django.db.models import Count, Q
from .helpers import get_current_month_dates
import json

def generate_weekly_report(request):
    print('weekly report requested........')
    today = now().date()
    start_date = today - timedelta(days=today.weekday() + 7)
    end_date = start_date + timedelta(days=6)

    tickets = Ticket.objects.filter(created_at__range=[start_date, today+timedelta(days=1)])
    support_members = SupportMember.objects.all()
    inquirers = Inquirer.objects.all()
    
    report_data = []

    # Calculate totals and daily statistics
    total_opened = tickets.filter(status='open').count()
    total_closed = tickets.filter(status='closed').count()
    total_resolved = tickets.filter(status='resolved').count()
    
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
        average_time = f"{average_time_hours:.2f} hours"  # Format it as needed
        
        report_data.append({
            'member': member.username,
            'resolved_count': total_resolved_count,
            'pending_count': pending_tickets_count,
            'closed_count': total_closed_count,
            'average_time': average_time
        })

    # Additional statistics
    branch_stats = tickets.values('branch_opened').annotate(
        tickets=Count('id')
    ).order_by('branch_opened')

    branch_most_inquiries = branch_stats.first()
    total_inquiries = branch_stats.aggregate(total=Count('id'))['total']

    context = {
        'report_data': report_data,
        'start_date': start_date,
        'end_date': end_date,
        'total_opened': total_opened,
        'total_pending': tickets.filter(status='pending').count(),
        'total_closed': total_closed,
        'total_resolved': total_resolved,
        'daily_counts': daily_counts,
        'day_most_opened': day_most_opened,
        'day_most_closed': day_most_closed,
        'day_most_pending': day_most_pending,
        'day_most_resolved': day_most_resolved,
        'branch_most_inquiries': branch_most_inquiries,
        'total_inquiries': total_inquiries,
    }
    
    html_string = render_to_string('reports/weekly_report.html', context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="weekly_report.pdf"'
    return response

def generate_monthly_report(request):
    print('monthly report requested........')
    data = json.loads(request.body)
    start_date = data.get('start_date',datetime.now().date())
    # Get start and end dates from the request or set default dates
    start_date, end_date = get_current_month_dates(start_date)

    tickets = Ticket.objects.filter(created_at__range=[start_date, end_date])
    support_members = SupportMember.objects.all()
    branch_stats = tickets.values('branch_opened').annotate(
        tickets=Count('id')
    ).order_by('branch_opened')
    ticket_counts = tickets.values('branch_opened').annotate(
        open_count=Count('id', filter=Q(status='open')),
        pending_count=Count('id', filter=Q(status='pending')),
        closed_count=Count('id', filter=Q(status='closed')),
        resolved_count=Count('id', filter=Q(status='resolved'))
    )

    branch_most_inquiries = branch_stats.first()
    total_inquiries = branch_stats.aggregate(total=Count('id'))['total']

    report_data = []

    # Calculate totals and daily statistics
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

    context = {
        'branch_stats': branch_stats,
        'ticket_counts': ticket_counts,
        'branch_most_inquiries': branch_most_inquiries,
        'total_inquiries': total_inquiries,
        'report_data': report_data,
        'start_date': datetime.strftime(start_date,'%d %B %Y'),
        'end_date': datetime.strftime(end_date,'%d %B %Y'),
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
    
    html_string = render_to_string('reports/monthly_report.html', context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="monthly_report.pdf"'
    return response

def generate_overall_report(request):
    print('overall report requested........')
    today = now().date()
    data = json.loads(request.body)
    start_date = data.get('start_date', '2001-01-01')
    end_date = data.get('end_date', '2050-12-31')
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = datetime(2001, 1, 1).date()
        end_date = datetime(2050, 12, 31).date()
    tickets = Ticket.objects.filter(created_at__range=[start_date, end_date])
    support_members = SupportMember.objects.all()
    inquirers = Inquirer.objects.all()
    
    report_data = []

    # Calculate totals and daily statistics
    total_opened = tickets.filter(status='open').count()
    total_closed = tickets.filter(status='closed').count()
    total_resolved = tickets.filter(status='resolved').count()
    
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
        average_time = f"{average_time_hours:.2f} hours"  # Format it as needed
        
        report_data.append({
            'member': member.username,
            'resolved_count': total_resolved_count,
            'pending_count': pending_tickets_count,
            'closed_count': total_closed_count,
            'average_time': average_time
        })

    # Additional statistics
    branch_stats = tickets.values('branch_opened').annotate(
        tickets=Count('id')
    ).order_by('branch_opened')
    ticket_counts = Ticket.objects.values('branch_opened').annotate(
        open_count=Count('id', filter=Q(status='open')),
        pending_count=Count('id', filter=Q(status='pending')),
        closed_count=Count('id', filter=Q(status='closed')),
        resolved_count=Count('id', filter=Q(status='resolved'))
    )

    branch_most_inquiries = branch_stats.first()
    total_inquiries = branch_stats.aggregate(total=Count('id'))['total']

    context = {
        'report_data': report_data,
        'start_date': start_date,
        'end_date': end_date,
        'today': datetime.now().strftime('%d %B %Y'),
        'total_opened': total_opened,
        'total_pending': tickets.filter(status='pending').count(),
        'total_closed': total_closed,
        'total_resolved': total_resolved,
        'ticket_counts':ticket_counts,
        'daily_counts': daily_counts,
        'day_most_opened': day_most_opened,
        'day_most_closed': day_most_closed,
        'day_most_pending': day_most_pending,
        'day_most_resolved': day_most_resolved,
        'branch_most_inquiries': branch_most_inquiries,
        'total_inquiries': total_inquiries,
    }
    
    html_string = render_to_string('reports/overall_report.html', context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="overall_report.pdf"'
    return response

def generate_branch_report(request):
    print('branch reported requested........')
    data = json.loads(request.body)
    start_date = data.get('start_date', '2001-01-01')
    end_date = data.get('end_date', '2050-12-31')
    branch_id = data.get('branch')
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = datetime(2001, 1, 1).date()
        end_date = datetime(2050, 12, 31).date()
    branch = Branch.objects.get(id=branch_id)
    tickets = Ticket.objects.filter(branch_opened__icontains=branch.name, created_at__range=[start_date, end_date])
    branch_stats = tickets.values('branch_opened').annotate(
            tickets=Count('id')
        ).order_by('branch_opened')
    closed_tickets_count = tickets.filter(status='closed').count()
    open_tickets_count = tickets.filter(status='open').count()
    resolved_tickets_count = tickets.filter(status='resolved').count()
    pending_tickets_count = tickets.filter(status='pending').count()

    total_inquiries = branch_stats.aggregate(total=Count('id'))['total']

    report_data = []
    for ticket in tickets:
        report_data.append({
            'title': ticket.title,
            
            'description': ticket.description,
            'created_by': ticket.created_by.username if ticket.created_by else 'N/A',
            'assigned_to': ticket.assigned_to.username if ticket.assigned_to else 'N/A',
            'branch_opened': ticket.branch_opened,
            'status': ticket.status,
            'created_at': ticket.created_at,
            'updated_at': ticket.updated_at,
            'resolved_at': ticket.resolved_at,
            'closed_at': ticket.closed_at,
            'expired_at': ticket.expired_at,
            'time_to_resolve': ticket.get_time_to_resolve(),
        })
    
    context = {
        'report_data': report_data, 
        'branch_name': 'branch_name',
        'open_count': open_tickets_count,
        'start_date': datetime.strftime(start_date,'%d %B %Y'),
        'end_date': datetime.strftime(end_date,'%d %B %Y'),
        'pending_count': pending_tickets_count,
        'closed_count': closed_tickets_count,
        'resolved_count': resolved_tickets_count,
        'branch': ticket.branch_opened,
        'total_inquiries': total_inquiries,
        }
    
    html_string = render_to_string('reports/branch_report.html', context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{'branch_name'}_report.pdf"'
    return response

def generate_support_member_report(request):
    print('support member report requested........')
    # Get start and end dates from the request or set default dates
    data = json.loads(request.body)
    start_date = data.get('start_date', '2001-01-01')
    end_date = data.get('end_date', '2050-12-31')
    support_member_id = data.get('support_member')
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = datetime(2001, 1, 1).date()
        end_date = datetime(2050, 12, 31).date()

    support_member = SupportMember.objects.get(id=support_member_id)
    tickets = Ticket.objects.filter(created_at__range=[start_date, end_date], assigned_to=support_member)

    report_data = []
    branch_stats = tickets.values('branch_opened').annotate(
        tickets=Count('id')
    ).order_by('branch_opened')
    ticket_counts = tickets.values('branch_opened').annotate(
        open_count=Count('id', filter=Q(status='open')),
        pending_count=Count('id', filter=Q(status='pending')),
        closed_count=Count('id', filter=Q(status='closed')),
        resolved_count=Count('id', filter=Q(status='resolved'))
    )

    branch_most_inquiries = branch_stats.first()
    total_inquiries = branch_stats.aggregate(total=Count('id'))['total']


    resolved_tickets = tickets.filter(status='resolved')
    closed_tickets = tickets.filter(status='closed')
    pending_tickets = tickets.filter(status='pending')
    
    total_opened = tickets.filter(status='open').count()
    total_closed = tickets.filter(status='closed').count()
    total_resolved = tickets.filter(status='resolved').count()
    total_pending = tickets.filter(status='pending').count()
    
    
    total_resolved_count = resolved_tickets.count()
    total_closed_count = closed_tickets.count()
    pending_tickets_count = pending_tickets.count()
    
    total_time = timedelta()
    resolved_ticket_count = 0
    
    for ticket in resolved_tickets:
        if ticket.resolved_at:
            total_time += ticket.resolved_at - ticket.created_at
            resolved_ticket_count += 1
    

    report_data.append({
        'member': support_member.username,
        'resolved_count': total_resolved_count,
        'pending_count': pending_tickets_count,
        'closed_count': total_closed_count,
        'total_time': total_time
    })

    context = {
        'support_member': support_member.username,
        'total_opened': total_opened,
        'total_pending': total_pending,
        'total_closed': total_closed,
        'total_resolved': total_resolved,
        'tickets': tickets,
        'ticket_counts': ticket_counts,
        'branch_stats': branch_stats,
        'branch_most_inquiries': branch_most_inquiries,
        'total_inquiries': total_inquiries,
        'report_data': report_data,
        'start_date': start_date,
        'end_date': end_date,
        'total_opened': tickets.filter(status='open').count(),
        'total_pending': tickets.filter(status='pending').count(),
        'total_closed': tickets.filter(status='closed').count(),
        'total_resolved': tickets.filter(status='resolved').count(),
    }
    
    html_string = render_to_string('reports/support_member_report.html', context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="support_member_report.pdf"'
    return response


