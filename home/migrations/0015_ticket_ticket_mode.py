# Generated by Django 5.0.7 on 2024-08-20 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_alter_message_inquirer_alter_message_support_member_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='ticket_mode',
            field=models.CharField(blank=True, default='other', max_length=20, null=True),
        ),
    ]