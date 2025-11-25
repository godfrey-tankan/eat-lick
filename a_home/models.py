from django.db import models
from django.contrib.auth.models import User


class Company(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    logo = models.ImageField(upload_to="company_logos/", null=True, blank=True)
    primary_color = models.CharField(max_length=7, default="#003366")
    secondary_color = models.CharField(max_length=7, default="#FF6600")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class CompanyAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    can_view_reports = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"


class SurveyQuestion(models.Model):
    QUESTION_CATEGORY_CHOICES = [
        # NHS Categories
        ("general_satisfaction", "General Satisfaction"),
        ("brand_awareness", "Brand Awareness"),
        ("service_quality", "Service Quality"),
        ("pricing_value", "Pricing and Value"),
        # HIT Categories
        ("vision_strategy", "Vision and Strategy"),
        ("job_satisfaction", "Job Satisfaction"),
        ("leadership", "Leadership and People Management"),
        ("conditions_service", "Conditions of Service"),
        ("communication", "Communication"),
        ("learning_development", "Learning Development"),
        ("organizational_culture", "Organizational Culture"),
        ("nature_work", "Nature of Work"),
        ("vigour", "Vigour"),
        ("dedication", "Dedication"),
        ("absorption", "Absorption"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    question_text = models.CharField(max_length=500)
    category = models.CharField(max_length=50, choices=QUESTION_CATEGORY_CHOICES)
    required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["company", "order", "id"]

    def __str__(self):
        return f"{self.company.code}: {self.question_text}"


class SurveyResponse(models.Model):
    RESPONSE_CHOICES = [
        (1, "Strongly disagree"),
        (2, "Disagree"),
        (3, "Neutral"),
        (4, "Agree"),
        (5, "Strongly agree"),
    ]

    user_id = models.CharField(max_length=100)  # Anonymous user ID
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    response = models.IntegerField(choices=RESPONSE_CHOICES)
    response_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user_id", "question"]


class DemographicData(models.Model):
    # Common fields
    user_id = models.CharField(max_length=100)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="demographics",
    )
    response_date = models.DateTimeField(auto_now_add=True)

    # NHS specific fields
    client_type = models.CharField(max_length=100, blank=True, null=True)

    # HIT specific fields
    gender = models.CharField(max_length=10, blank=True, null=True)
    age_group = models.CharField(max_length=50, blank=True, null=True)
    work_experience = models.CharField(max_length=50, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    contract_type = models.CharField(max_length=50, blank=True, null=True)
    designation = models.CharField(max_length=50, blank=True, null=True)
    highest_qualification = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(
        max_length=50, blank=True, null=True
    )  # Academic/Non-academic

    def __str__(self):
        return f"{self.company.name} - {self.user_id}"


# Create your models here.
class JobSatisfactionQuestion(models.Model):
    QUESTION_CATEGORY_CHOICES = [
        ("pay", "Pay"),
        ("promotion", "Promotion"),
        ("supervision", "Supervision"),
        ("fringe_benefits", "Fringe Benefits"),
        ("contingent_rewards", "Contingent Rewards"),
        ("operating_conditions", "Operating Conditions"),
        ("coworkers", "Coworkers"),
        ("nature_of_work", "Nature of Work"),
        ("communication", "Communication"),
        ("health_and_safety", "Health and Safety"),
        ("vigour_energy", "Vigour and Energy"),
        ("dedication", "Dedication"),
        ("absorption", "Absorption"),
    ]
    question_text = models.CharField(max_length=500)
    category = models.CharField(max_length=50, choices=QUESTION_CATEGORY_CHOICES)
    required = models.BooleanField(default=True)  # Mandatory or optional

    def __str__(self):
        return self.question_text


class LikertScaleAnswer(models.Model):
    RESPONSE_CHOICES = [
        (1, "Disagree very much"),
        (2, "Disagree moderately"),
        (3, "Disagree slightly"),
        (4, "Agree slightly"),
        (5, "Agree moderately"),
        (6, "Agree very much"),
    ]

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(
        JobSatisfactionQuestion, related_name="answers", on_delete=models.CASCADE
    )
    response = models.IntegerField(choices=RESPONSE_CHOICES, null=True, blank=True)
    response_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to {self.question.question_text}: {self.get_response_display()}"


class DemographicDataold(models.Model):
    GENDER_CHOICES = [("male", "Male"), ("female", "Female")]

    AGE_GROUP_CHOICES = [
        ("before_1966", "Before 1966"),
        ("1966_1976", "1966-1976"),
        ("1977_1994", "1977-1994"),
        ("after_1994", "After 1994"),
    ]

    EXPERIENCE_CHOICES = [
        ("less_than_1", "Less than 1 year"),
        ("1_to_5", "1 to 5 years"),
        ("5_to_10", "5 to 10 years"),
        ("10_to_15", "10 to 15 years"),
        ("over_15", "Over 15 years"),
    ]

    QUALIFICATION_CHOICES = [
        ("o_level", "O Level"),
        ("a_level", "A Level"),
        ("diploma", "Diploma/Professional Qualifications"),
        ("degree", "Degree"),
        ("post_grad", "Post Graduate"),
    ]

    DESIGNATION_CHOICES = [
        ("director", "Director"),
        ("manager", "Manager"),
        ("assistant_manager", "Assistant Manager"),
        ("non_managerial", "Non-managerial"),
    ]

    DEPARTMENT_CHOICES = [
        ("home_link_money_transfers", "Homelink Money Transfers"),
        ("homelink_finance", "Homelink Finance"),
        ("projects_and_mortgages", "Projects And Mortgages"),
        ("finance_and_investments", "Finance And Investments"),
        ("support_services", "Support Services"),
        ("security", "Security"),
    ]

    DIVISION_CHOICES = [
        ("homelink_finance", "Homelink Finance"),
        ("money_transfers", "Money Transfers"),
        ("head_office", "Head Office"),
    ]

    CONTRACT_CHOICES = [
        ("permanent", "Permanent"),
        ("contract", "Contract"),
        ("relief", "Relief"),
    ]

    LOCATION_CHOICES = [
        ("harare", "Harare"),
        ("kwekwe", "Kwekwe"),
        ("gweru", "Gweru"),
        ("bulawayo", "Bulawayo"),
        ("mutare_and_rusape", "Mutare and Rusape"),
    ]

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, default="male")
    age_group = models.CharField(
        max_length=50, choices=AGE_GROUP_CHOICES, default="20_below"
    )
    work_experience = models.CharField(
        max_length=50, choices=EXPERIENCE_CHOICES, default="5_below"
    )
    highest_qualification = models.CharField(
        max_length=50, choices=QUALIFICATION_CHOICES, default="o_level"
    )
    designation = models.CharField(
        max_length=50, choices=DESIGNATION_CHOICES, default="line_employees"
    )
    department = models.CharField(
        max_length=100, choices=DEPARTMENT_CHOICES, default="MKT"
    )
    contract_type = models.CharField(
        max_length=50, choices=CONTRACT_CHOICES, default="permanent"
    )
    response_date = models.DateTimeField(auto_now_add=True)
    division = models.CharField(
        max_length=50, choices=DIVISION_CHOICES, blank=True, null=True
    )
    location = models.CharField(
        max_length=50, choices=LOCATION_CHOICES, blank=True, null=True
    )

    def __str__(self):
        return f"{self.gender}, {self.age_group}, {self.designation}"
