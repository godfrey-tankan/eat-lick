
from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id','title', 'status', 'created_at', 'assigned_to']
    search_fields = ['title', 'status']
    list_filter = ['status', 'created_at', 'updated_at']

@admin.register(TicketLog)
class TicketLogAdmin(admin.ModelAdmin):
    list_display = ['ticket','id']
    search_fields = ['ticket', 'action']

# @admin.register(Comment)
# class CommentAdmin(admin.ModelAdmin):
#     list_display = ['id','ticket', 'user', 'created_at']
#     search_fields = ['ticket', 'user']
#     list_filter = ['created_at']

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'answer', 'created_at']
    search_fields = ['question', 'answer']
    list_filter = ['created_at']

@admin.register(SupportMember)
class SupportMemberAdmin(admin.ModelAdmin):
    list_display = ['id','username', 'is_active','phone_number']
    search_fields = ['username']
    list_filter = ['is_active','is_deleted']
    
@admin.register(Inquirer)
class InquirerAdmin(admin.ModelAdmin):
    list_display = ['id','username', 'is_active','phone_number']
    search_fields = ['username']
    list_filter = ['is_active','is_deleted']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id','inquirer']
    search_fields = ['inquirer']
    list_filter = ['created_at']