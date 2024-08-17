from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now

# Create your models here.

User = get_user_model()

class Inquirer(models.Model):
    username = models.CharField(max_length=255,null=True, blank=True,default='Inquirer')
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    user_mode = models.CharField(max_length=20, null=True, blank=True)
    user_status = models.CharField(max_length=20, null=True, blank=True)
    branch = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Inquirer: {self.username}"


class SupportMember(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=255,null=True, blank=True,default='Support')
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    user_mode = models.CharField(max_length=20, null=True, blank=True,default='ticket_acceptance')
    user_status = models.CharField(max_length=20, null=True, blank=True,default='ticket_acceptance')
    branch = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Support Member: {self.username}"


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'open'),
        ('pending', 'pending'),
        ('closed', 'closed'),
        ('expired', 'expired'),
        ('resolved', 'resolved'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(Inquirer, related_name='tickets', on_delete=models.DO_NOTHING, null=True, blank=True)
    branch_opened = models.CharField(max_length=20, null=True, blank=True)
    assigned_to = models.ForeignKey(SupportMember, related_name='assigned_tickets', on_delete=models.DO_NOTHING, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    
    def get_time_to_resolve(self):
        if self.resolved_at:
            time_diff = self.resolved_at - self.created_at
        elif self.closed_at:
            time_diff = self.closed_at - self.created_at
        else:
            return "Not resolved yet"

        weeks, days = divmod(time_diff.days, 7)
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        result = []
        if weeks > 0:
            result.append(f"{weeks} weeks")
        if days > 0:
            result.append(f"{days} days")
        if hours > 0:
            result.append(f"{hours} hours")
        if minutes > 0:
            result.append(f"{minutes} minutes")
        
        return ', '.join(result) if result else "Less than a minute"
    def get_time_to_resolve_duration(self):
        end_time = self.resolved_at or self.closed_at or now()
        return end_time - self.created_at
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
class Message(models.Model):
    inquirer = models.ForeignKey(Inquirer, related_name='messages', on_delete=models.DO_NOTHING, null=True, blank=True)
    support_member = models.ForeignKey(SupportMember, related_name='messages', on_delete=models.DO_NOTHING, null=True, blank=True)
    image_message = models.ImageField(upload_to='images/', null=True, blank=True)
    image_name = models.CharField(max_length=255, null=True, blank=True)
    audio_message = models.FileField(upload_to='audio/', null=True, blank=True)
    audio_name = models.CharField(max_length=255, null=True, blank=True)
    document_message = models.FileField(upload_to='documents/', null=True, blank=True)
    document_name = models.CharField(max_length=255, null=True, blank=True)
    ticket_id = models.ForeignKey(Ticket, related_name='messages', on_delete=models.DO_NOTHING, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message #{self.content[:20]}"

class Branch(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)

    def __str__(self):
        return f"Branch: {self.name}"