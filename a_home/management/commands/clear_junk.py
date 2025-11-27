from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from a_home.models import Company, SurveyQuestion, CompanyAdmin, SurveyResponse


class Command(BaseCommand):
    help = "Setup complete survey system with all questions and companies"

    def handle(self, *args, **options):
        self.stdout.write("Setting up survey system...")

        # clear all old data
        SurveyResponse.objects.all().delete()
