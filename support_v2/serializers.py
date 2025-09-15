from rest_framework import serializers
from django.contrib.auth import get_user_model
from home.models import (
    Inquirer, SupportMember, Ticket, TicketLog, 
    Comment, FAQ, Message, Branch
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'is_staff', 'is_superuser']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class InquirerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquirer
        fields = '__all__'

class SupportMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    
    class Meta:
        model = SupportMember
        fields = '__all__'

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    created_by_details = InquirerSerializer(source='created_by', read_only=True)
    assigned_to_details = SupportMemberSerializer(source='assigned_to', read_only=True)
    time_to_resolve = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    is_escalated = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = '__all__'
    
    def get_time_to_resolve(self, obj):
        return obj.get_time_to_resolve()
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_is_escalated(self, obj):
        return obj.logs.filter(changed_by__icontains='escalated').exists()

class TicketLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketLog
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    user_details = serializers.CharField(source='user', read_only=True)
    
    class Meta:
        model = Comment
        fields = '__all__'

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    inquirer_details = InquirerSerializer(source='inquirer', read_only=True)
    support_member_details = SupportMemberSerializer(source='support_member', read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'

# Dashboard serializers
class SupportMemberStatsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    total_resolved = serializers.IntegerField()
    total_closed_tickets = serializers.IntegerField()
    total_pending_tickets = serializers.IntegerField()
    total_assigned_tickets = serializers.IntegerField()
    average_rating = serializers.FloatField()
    percentage_resolved = serializers.FloatField()
    percentage_pending = serializers.FloatField()
    percentage_closed = serializers.FloatField()
    percentage_expired = serializers.FloatField()

class DashboardStatsSerializer(serializers.Serializer):
    tickets_count = serializers.IntegerField()
    open_tickets_count = serializers.IntegerField()
    closed_tickets_count = serializers.IntegerField()
    pending_tickets_count = serializers.IntegerField()
    resolved_tickets_count = serializers.IntegerField()
    open_tickets_percentage = serializers.FloatField()
    closed_tickets_percentage = serializers.FloatField()
    pending_tickets_percentage = serializers.FloatField()
    resolved_tickets_percentage = serializers.FloatField()
    active_support_members = serializers.IntegerField()

class ChartDataSerializer(serializers.Serializer):
    labels_weekly = serializers.ListField(child=serializers.CharField())
    resolved_counts_weekly = serializers.ListField(child=serializers.IntegerField())
    open_counts_weekly = serializers.ListField(child=serializers.IntegerField())
    closed_counts_weekly = serializers.ListField(child=serializers.IntegerField())
    pending_counts_weekly = serializers.ListField(child=serializers.IntegerField())
    labels_monthly = serializers.ListField(child=serializers.CharField())
    resolved_counts_monthly = serializers.ListField(child=serializers.IntegerField())
    open_counts_monthly = serializers.ListField(child=serializers.IntegerField())
    closed_counts_monthly = serializers.ListField(child=serializers.IntegerField())
    pending_counts_monthly = serializers.ListField(child=serializers.IntegerField())