# Generated by Django 5.0.7 on 2024-09-16 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0017_ticket_queued_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='inquiry_type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]