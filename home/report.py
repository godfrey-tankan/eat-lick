import io
import pandas as pd
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import timedelta
from django.utils.timezone import now
from .models import Ticket, SupportMember

def generate_weekly_report(request):
    # Define the start and end dates for the past week
    today = now().date()
    start_date = today - timedelta(days=today.weekday() + 7)  # Start of the previous week
    end_date = start_date + timedelta(days=6)  # End of the previous week

    # Get tickets for the week
    tickets = Ticket.objects.filter(created_at__range=[start_date, end_date])
    
    # Get support members
    support_members = SupportMember.objects.all()
    
    # Initialize data structures
    report_data = []
    
    for member in support_members:
        tickets_for_member = tickets.filter(assigned_to=member)
        resolved_tickets = tickets_for_member.filter(status='resolved')
        closed_tickets = tickets_for_member.filter(status='closed')
        
        total_resolved = resolved_tickets.count()
        total_closed = closed_tickets.count()
        
        total_time = timedelta()
        resolved_ticket_count = 0
        
        for ticket in resolved_tickets:
            if ticket.resolved_at:
                total_time += ticket.resolved_at - ticket.created_at
                resolved_ticket_count += 1
        
        average_time = (total_time / resolved_ticket_count) if resolved_ticket_count > 0 else timedelta(0)
        
        report_data.append({
            'member': member.username,
            'resolved_count': total_resolved,
            'closed_count': total_closed,
            'average_time': average_time
        })
    
    # Generate PDF
    html_string = render_to_string('reports/weekly_report.html', {'report_data': report_data, 'start_date': start_date, 'end_date': end_date})
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="weekly_report.pdf"'
    return response