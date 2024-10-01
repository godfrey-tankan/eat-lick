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
        help_texts = {
            'username': 'This will be used as support member username on WhatsApp.',
            'phone_number': 'Provide the support member\'s phone number, including the country code.',
            'is_active': 'Check this box if the support member is allowed to use the chatbot.',
        }

    # Override fields to add help texts
    def __init__(self, *args, **kwargs):
        super(SupportMemberForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = self.Meta.help_texts['username']
        self.fields['phone_number'].help_text = self.Meta.help_texts['phone_number']
        self.fields['is_active'].help_text = self.Meta.help_texts['is_active']
        

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser']
        help_texts = {
            'username': 'Enter a unique username that will be used to log in.',
            'first_name': 'Enter the first name of the user.',
            'last_name': 'Enter the last name of the user.',
            'email': 'Provide a valid email address for the user.',
            'is_active': 'Check this box if the user account is active.',
            'is_staff': 'Check this box if the user should have access to this admin dashboard.',
            'is_superuser': 'Check this box if the user has all permissions without explicitly assigning them.',
        }

    # Override fields to add help texts
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = self.Meta.help_texts['username']
        self.fields['first_name'].help_text = self.Meta.help_texts['first_name']
        self.fields['last_name'].help_text = self.Meta.help_texts['last_name']
        self.fields['email'].help_text = self.Meta.help_texts['email']
        self.fields['is_active'].help_text = self.Meta.help_texts['is_active']
        self.fields['is_staff'].help_text = self.Meta.help_texts['is_staff']
        self.fields['is_superuser'].help_text = self.Meta.help_texts['is_superuser']