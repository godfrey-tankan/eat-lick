from django.urls import path

from . import views
from .handle_branches import *
from .handle_tickets import *

urlpatterns = [
    path('', views.home_view, name='home'),
    path('enlsupport/', views.index, name='index'),
    path('branches/', get_branches, name='get_branches'),
    path('branches/add/', add_branch, name='add_branch'),
    path('branches/update/<int:branch_id>/', update_branch, name='update_branch'),
    path('branches/delete/<int:branch_id>/', delete_branch, name='delete_branch'),
    path('create/', api_create_ticket, name='api_create_ticket'),
    path('get_support_members/', get_support_members, name='get_support_members'),
]
