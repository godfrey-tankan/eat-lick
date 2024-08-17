# Generated by Django 5.0.7 on 2024-08-17 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0009_message_image_message_message_image_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='audio_message',
            field=models.FileField(blank=True, null=True, upload_to='audio/'),
        ),
        migrations.AddField(
            model_name='message',
            name='audio_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='document_message',
            field=models.FileField(blank=True, null=True, upload_to='documents/'),
        ),
        migrations.AddField(
            model_name='message',
            name='document_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]