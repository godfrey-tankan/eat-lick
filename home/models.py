from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.

User = get_user_model()

class SupportMember(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=255,null=True, blank=True,default='Support')
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    user_mode = models.CharField(max_length=20, null=True, blank=True)
    user_status = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Support Member: {self.id}"

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
        ('expired', 'Expired'),
        ('resolved', 'Resolved'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    assigned_to = models.ForeignKey(SupportMember, related_name='assigned_tickets', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.title} ({self.status})"


class TicketLog(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='logs', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Ticket.STATUS_CHOICES)
    changed_by = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log #{self.id} - Ticket #{self.ticket.id} status changed to {self.status}"

class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='comments', on_delete=models.CASCADE)
    user = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment #{self.id} by {self.user.username} on Ticket #{self.ticket.id}"
class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('billing', 'Billing'),
        ('technical', 'Technical'),
        ('account', 'Account'),
    ]
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FAQ: {self.question}"