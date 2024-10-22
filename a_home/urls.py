from django.urls import path, include
from a_home.views import *

urlpatterns = [
    path('', home_view, name='home'),
    path('start/', demographic_data_view, name='start'),
    path('thank-you/', thank_you, name='thank_you'),
    path('job-satisfaction/', job_satisfaction_view, name='job_satisfaction'),
    path('aggregated-feedback/', aggregated_feedback_view, name='aggregated_feedback'),
    path('smedco/staff/', staff_dashboard_view, name='staff_dashboard'),
    path('feedbacks/', feedback_list, name='feedback_list'),
    path('feedbacks/details/', feedback_detail, name='feedback_detail'),
    path('feedback/<int:user_id>/details/', feedback_details, name='detailed_feedback_page'),
     path('feedback/<int:user_id>/details/', get_user_feedback, name='user_feedback_details'),
    # path('members/',test,name='members')
    
]