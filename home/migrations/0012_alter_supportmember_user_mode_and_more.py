# Generated by Django 5.0.7 on 2024-08-17 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0011_branch'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supportmember',
            name='user_mode',
            field=models.CharField(blank=True, default='ticket_acceptance', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='supportmember',
            name='user_status',
            field=models.CharField(blank=True, default='ticket_acceptance', max_length=20, null=True),
        ),
    ]