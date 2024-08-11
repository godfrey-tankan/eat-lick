from rest_framework import serializers
from .models import Ticket, TicketLog, Comment, FAQ

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'

class TicketLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketLog
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'
