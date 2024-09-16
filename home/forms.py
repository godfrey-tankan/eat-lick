from django import forms
from .models import Ticket, Comment,SupportMember
from django.contrib.auth import get_user_model

User = get_user_model()

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'assigned_to'] 

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']  

class SupportMemberForm(forms.ModelForm):
    class Meta:
        model = SupportMember
        fields = ['username', 'phone_number', 'is_active'] 

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username','first_name','last_name', 'email','is_active','is_staff','is_superuser']