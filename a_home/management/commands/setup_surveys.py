from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from a_home.models import Company, SurveyQuestion, CompanyAdmin


class Command(BaseCommand):
    help = "Setup complete survey system with all questions and companies"

    def handle(self, *args, **options):
        self.stdout.write("Setting up survey system...")

        self.clear_all_data()

        # Create Companies
        nhs_company = self.create_nhs_company()
        hit_company = self.create_hit_company()

        # Create Survey Questions
        self.create_nhs_questions(nhs_company)
        self.create_hit_questions(hit_company)

        # Create Admin Users
        self.create_admin_users(nhs_company, hit_company)

        self.stdout.write(
            self.style.SUCCESS("Successfully setup complete survey system!")
        )

    def create_nhs_company(self):
        company, created = Company.objects.get_or_create(
            code="NHS",
            defaults={
                "name": "National Handling Services",
                "primary_color": "#003366",
                "secondary_color": "#FF6600",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(f"Created NHS company")
        return company

    def clear_all_data(self):
        from a_home.models import DemographicData, SurveyResponse

        try:
            DemographicData.objects.all().delete()
            SurveyResponse.objects.all().delete()
        except Exception as e:
            print("error clearing old data....")

    def create_hit_company(self):
        company, created = Company.objects.get_or_create(
            code="HIT",
            defaults={
                "name": "Harare Institute of Technology",
                "primary_color": "#2E8B57",
                "secondary_color": "#FFD700",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(f"Created HIT company")
        return company

    def create_nhs_questions(self, company):
        questions_data = [
            # GENERAL SATISFACTION WITH NHS SERVICE
            (
                "I am generally happy with the service I get at NHS",
                "general_satisfaction",
                1,
            ),
            ("Staff members at NHS are generally helpful", "general_satisfaction", 2),
            (
                "The staff members at NHS are generally cheerful towards travellers/clients",
                "general_satisfaction",
                3,
            ),
            ("The service at NHS meets my expectations", "general_satisfaction", 4),
            ("The service at NHS is very consistent", "general_satisfaction", 5),
            (
                "I am very satisfied with the check in process at NHS",
                "general_satisfaction",
                6,
            ),
            (
                "The departure lounge was clean and service was good",
                "general_satisfaction",
                7,
            ),
            (
                "The staff members at NHS are professional and helpful",
                "general_satisfaction",
                8,
            ),
            (
                "Given the choice, I will choose to use NHS always",
                "general_satisfaction",
                9,
            ),
            (
                "I get value for money when I use NHS as my service provider",
                "general_satisfaction",
                10,
            ),
            (
                "I would recommend NHS to friends and colleagues",
                "general_satisfaction",
                11,
            ),
            # BRAND AWARENESS AND VISIBILITY
            (
                "I already knew about NHS before I interacted with them",
                "brand_awareness",
                12,
            ),
            (
                "They live true to their promise of being the Hostess on the ground",
                "brand_awareness",
                13,
            ),
            ("I am aware of their full range of services", "brand_awareness", 14),
            ("The NHS Brand is strong and well known out there", "brand_awareness", 15),
            ("Other service providers talk good about NHS", "brand_awareness", 16),
            ("The NHS brand is known for great service", "brand_awareness", 17),
            ("I always think favorably about the NHS brand", "brand_awareness", 18),
            # SERVICE QUALITY
            ("NHS handles clients well", "service_quality", 19),
            (
                "The staff members are professional and respectful",
                "service_quality",
                20,
            ),
            (
                "The staff members attend to clients in a timely manner",
                "service_quality",
                21,
            ),
            (
                "The staff members provided me with all the information I needed",
                "service_quality",
                22,
            ),
            (
                "They managed to meet my expectations of the service",
                "service_quality",
                23,
            ),
            (
                "The staff members are willing to go the extra mile to make the client happy",
                "service_quality",
                24,
            ),
            # PRICING AND VALUE FOR MONEY
            ("I have never been asked to pay extra fees", "pricing_value", 25),
            (
                "I have never been asked to pay a bribe by NHS staff members",
                "pricing_value",
                26,
            ),
        ]

        created_count = 0
        for question_text, category, order in questions_data:
            question, created = SurveyQuestion.objects.get_or_create(
                company=company,
                question_text=question_text,
                defaults={"category": category, "order": order, "required": True},
            )
            if created:
                created_count += 1

        self.stdout.write(f"Created {created_count} NHS questions")

    def create_hit_questions(self, company):
        questions_data = [
            # VISION AND STRATEGIC DIRECTION OF HIT
            ("I understand my role at HIT", "vision_strategy", 1),
            ("I know the strategic direction of HIT", "vision_strategy", 2),
            ("I believe in the vision of HIT", "vision_strategy", 3),
            (
                "The vision of HIT is shared well with all employees",
                "vision_strategy",
                4,
            ),
            ("All processes at HIT are done in a proper way", "vision_strategy", 5),
            # JOB SATISFACTION
            ("I am satisfied with my current role at HIT", "job_satisfaction", 6),
            (
                "I am able to maintain a healthy work-life balance in my role",
                "job_satisfaction",
                7,
            ),
            (
                "My Superior/Team Leader provides clear growth within HIT",
                "job_satisfaction",
                8,
            ),
            ("I am being paid a fair amount for the work I do", "job_satisfaction", 9),
            (
                "The level of communication at HIT is satisfactory",
                "job_satisfaction",
                10,
            ),
            (
                "The overall working environment at HIT is positive",
                "job_satisfaction",
                11,
            ),
            (
                "I have the tools and resources to perform my job effectively",
                "job_satisfaction",
                12,
            ),
            # LEADERSHIP AND PEOPLE MANAGEMENT
            ("MY Superior/Team Leader effectively leads the team", "leadership", 13),
            (
                "My superior/Team Leader gives me the support I need to succeed in my role",
                "leadership",
                14,
            ),
            (
                "My Superior/Team leader gives me constructive and regular feedback on my performance",
                "leadership",
                15,
            ),
            (
                "My Superior/Team Leader acknowledges and appreciates my contribution at work",
                "leadership",
                16,
            ),
            (
                "I feel empowered to make decisions within the scope of my role",
                "leadership",
                17,
            ),
            (
                "I feel that HIT leaders represent the Organisation's core values",
                "leadership",
                18,
            ),
            # CONDITIONS OF SERVICE, SAFETY, HEALTH AND ENVIRONMENT
            ("I am satisfied with the benefits I receive", "conditions_service", 19),
            (
                "The benefits we receive are as good as most other organizations offer",
                "conditions_service",
                20,
            ),
            (
                "We receive all the benefits that we are supposed to be given",
                "conditions_service",
                21,
            ),
            ("My working environment is safe and secure", "conditions_service", 22),
            (
                "I have adequate uniforms to look good when I am at work",
                "conditions_service",
                23,
            ),
            (
                "I have adequate protective clothing required for me to do my work",
                "conditions_service",
                24,
            ),
            ("My job is less stressful", "conditions_service", 25),
            (
                "The Company has programmes promoting employee wellness",
                "conditions_service",
                26,
            ),
            # COMMUNICATION
            ("There are clear channels of communication at HIT", "communication", 27),
            (
                "There is a free and open flow of work information to me from my superior/team leader",
                "communication",
                28,
            ),
            (
                "There is a free and open flow of information between the different work groups or departments",
                "communication",
                29,
            ),
            ("I am not afraid to express myself at HIT", "communication", 30),
            (
                "I get information on time to help me perform my job/duties",
                "communication",
                31,
            ),
            ("My work assignments are fully explained to me", "communication", 32),
            # LEARNING DEVELOPMENT
            (
                "HIT provides me with opportunities for career development (Training)",
                "learning_development",
                33,
            ),
            (
                "HIT provides me with opportunities for career advancement",
                "learning_development",
                34,
            ),
            (
                "HIT encourages employees to keep advancing themselves through further education",
                "learning_development",
                35,
            ),
            # ORGANISATIONAL CULTURE/WORK CULTURE
            ("HIT has a strong work culture", "organizational_culture", 36),
            (
                "The work culture at HIT drives performance and execution of goals",
                "organizational_culture",
                37,
            ),
            (
                "I believe there is gender diversity at HIT",
                "organizational_culture",
                38,
            ),
            # NATURE OF WORK
            ("I feel that my job is very meaningful", "nature_work", 39),
            ("I like doing the things I do at work", "nature_work", 40),
            ("I feel a sense of pride in doing my job", "nature_work", 41),
            # JOB ENGAGEMENT - VIGOUR
            ("At my work, I feel bursting with energy", "vigour", 42),
            ("At my job, I feel strong and vigorous", "vigour", 43),
            ("When I get up in the morning, I feel like going to work", "vigour", 44),
            # JOB ENGAGEMENT - DEDICATION
            ("I am enthusiastic about my job", "dedication", 45),
            ("My job inspires me", "dedication", 46),
            ("I am proud of the work that I do", "dedication", 47),
            # JOB ENGAGEMENT - ABSORPTION
            ("When I am working, I forget everything else around me", "absorption", 48),
            ("I feel happy when I am working intensely", "absorption", 49),
            ("I am immersed in my work", "absorption", 50),
        ]

        created_count = 0
        for question_text, category, order in questions_data:
            question, created = SurveyQuestion.objects.get_or_create(
                company=company,
                question_text=question_text,
                defaults={"category": category, "order": order, "required": True},
            )
            if created:
                created_count += 1

        self.stdout.write(f"Created {created_count} HIT questions")

    def create_admin_users(self, nhs_company, hit_company):
        # Create NHS Admin
        nhs_admin, created = User.objects.get_or_create(
            username="nhsadmin",
            defaults={
                "email": "admin@nhs.com",
                "first_name": "NHS",
                "last_name": "Administrator",
                "is_staff": True,
            },
        )
        if created:
            nhs_admin.set_password("nhsadmin123")
            nhs_admin.save()
            CompanyAdmin.objects.create(user=nhs_admin, company=nhs_company)
            self.stdout.write("Created NHS admin user: nhs_admin / nhsadmin123")

        # Create HIT Admin
        hit_admin, created = User.objects.get_or_create(
            username="hitadmin",
            defaults={
                "email": "admin@hit.com",
                "first_name": "HIT",
                "last_name": "Administrator",
                "is_staff": True,
            },
        )
        if created:
            hit_admin.set_password("hitadmin123")
            hit_admin.save()
            CompanyAdmin.objects.create(user=hit_admin, company=hit_company)
            self.stdout.write("Created HIT admin user: hitadmin / hitadmin123")
