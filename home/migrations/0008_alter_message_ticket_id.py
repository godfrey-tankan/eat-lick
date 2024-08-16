# Generated by Django 5.0.7 on 2024-08-16 07:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0007_alter_ticket_assigned_to_alter_ticket_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='ticket_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='messages', to='home.ticket'),
        ),
    ]