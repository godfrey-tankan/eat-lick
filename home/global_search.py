
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render
from .models import Ticket,SupportMember

def global_search(request):
    query = request.GET.get('q', '')
    users = tickets=support_members = None
    if query:
        if request.user.is_superuser:
            users = User.objects.filter(
                Q(username__icontains=query) | 
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
            tickets = Ticket.objects.filter(
                Q(description__icontains=query) |
                Q(status__icontains=query) |
                Q(created_by__username__icontains=query) |
                Q(assigned_to__username__icontains=query)
            )
            support_members = SupportMember.objects.filter(
                Q(user__username__icontains=query) |
                Q(user__email__icontains=query) |
                Q(phone_number__icontains=query) |
                Q(branch__icontains=query)
            )
        else:
            users = None
            tickets = Ticket.objects.filter(
                Q(description__icontains=query) |
                Q(status__icontains=query) |
                Q(created_by__username__icontains=query) |
                Q(assigned_to__username__iexact=request.user.id)
            )

    context = {
        'users': users,
        'tickets': tickets,
        'support_members': support_members,
        'query': query,
    }
    return render(request, 'search/search_results.html', context)
