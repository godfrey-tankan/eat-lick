from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import timedelta
from django.utils.timezone import now
from .models import Ticket, SupportMember, Inquirer
from django.db.models import Count, Q

def generate_weekly_report(request):
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
        'day_most_resolved': day_most_resolved,
        'branch_most_inquiries': branch_most_inquiries,
        'total_inquiries': total_inquiries,
    }
    
    html_string = render_to_string('reports/weekly_report.html', context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="weekly_report.pdf"'
    return response



# from django.http import HttpResponse
# from django.template.loader import render_to_string
# from weasyprint import HTML
# from datetime import timedelta
# from django.utils.timezone import now
# from .models import Ticket, SupportMember
# from django.db.models import Count, Q

# def generate_weekly_report(request):
#     today = now().date()
#     start_date = today - timedelta(days=today.weekday() + 7)
#     end_date = start_date + timedelta(days=6)

#     tickets = Ticket.objects.filter(created_at__range=[start_date, today+timedelta(days=1)])
#     support_members = SupportMember.objects.all()
    
#     report_data = []
    
#     # Calculate totals and daily statistics
#     total_opened = tickets.filter(status='open').count()
#     total_closed = tickets.filter(status='closed').count()
#     total_resolved = tickets.filter(status='resolved').count()
    
#     daily_counts = tickets.values('created_at__date').annotate(
#         opened=Count('id', filter=Q(status='open')),
#         closed=Count('id', filter=Q(status='closed')),
#         resolved=Count('id', filter=Q(status='resolved'))
#     ).order_by('created_at__date')
    
#     day_most_opened = daily_counts.order_by('-opened').first()
#     day_most_closed = daily_counts.order_by('-closed').first()
#     day_most_resolved = daily_counts.order_by('-resolved').first()
    
#     for member in support_members:
#         tickets_for_member = tickets.filter(assigned_to=member.id)
#         resolved_tickets = tickets_for_member.filter(status='resolved')
#         closed_tickets = tickets_for_member.filter(status='closed')
        
#         total_resolved_count = resolved_tickets.count()
#         total_closed_count = closed_tickets.count()
        
#         total_time = timedelta()
#         resolved_ticket_count = 0
        
#         for ticket in resolved_tickets:
#             if ticket.resolved_at:
#                 total_time += ticket.resolved_at - ticket.created_at
#                 resolved_ticket_count += 1
        
#         average_time_hours = (total_time.total_seconds() / 3600) / resolved_ticket_count if resolved_ticket_count > 0 else 0
#         average_time = f"{average_time_hours:.2f} hours"  # Format it as needed
        
#         report_data.append({
#             'member': member.username,
#             'resolved_count': total_resolved_count,
#             'closed_count': total_closed_count,
#             'average_time': average_time
#         })
    
#     context = {
#         'report_data': report_data,
#         'start_date': start_date,
#         'end_date': end_date,
#         'total_opened': total_opened,
#         'total_closed': total_closed,
#         'total_resolved': total_resolved,
#         'daily_counts': daily_counts,
#         'day_most_opened': day_most_opened,
#         'day_most_closed': day_most_closed,
#         'day_most_resolved': day_most_resolved,
#     }
    
#     html_string = render_to_string('reports/weekly_report.html', context)
#     pdf_file = HTML(string=html_string).write_pdf()

#     response = HttpResponse(pdf_file, content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="weekly_report.pdf"'
#     return response


