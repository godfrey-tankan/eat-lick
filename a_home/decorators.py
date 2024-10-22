from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .models import DemographicData, User  # Adjust your import paths

def check_user_feedback(view_func):
    def wrapper(request, *args, **kwargs):
        user = get_object_or_404(User, id=request.user.id)
        demographic_ob = DemographicData.objects.filter(user_id=user)
        if demographic_ob.exists():
            return render(request, 'review_submited.html')
        return view_func(request, *args, **kwargs)
    
    return wrapper