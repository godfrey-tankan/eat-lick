from django import forms
from .models import Ticket, Comment,SupportMember

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
        fields = ['username', 'phone_number','branch', 'is_active'] 