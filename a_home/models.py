from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class JobSatisfactionQuestion(models.Model):
    QUESTION_CATEGORY_CHOICES = [
        ('pay', 'Pay'),
        ('promotion', 'Promotion'),
        ('supervision', 'Supervision'),
        ('fringe_benefits', 'Fringe Benefits'),
        ('contingent_rewards', 'Contingent Rewards'),
        ('operating_conditions', 'Operating Conditions'),
        ('coworkers', 'Coworkers'),
        ('nature_of_work', 'Nature of Work'),
        ('communication', 'Communication'),
        ('health_and_safety', 'Health and Safety'),
        ('vigour_energy', 'Vigour and Energy'),
        ('dedication', 'Dedication'),
        ('absorption', 'Absorption'),
        
    ]
    question_text = models.CharField(max_length=500)
    category = models.CharField(max_length=50, choices=QUESTION_CATEGORY_CHOICES)
    required = models.BooleanField(default=True)  # Mandatory or optional

    def __str__(self):
        return self.question_text


class LikertScaleAnswer(models.Model):
    RESPONSE_CHOICES = [
        (1, 'Disagree very much'),
        (2, 'Disagree moderately'),
        (3, 'Disagree slightly'),
        (4, 'Agree slightly'),
        (5, 'Agree moderately'),
        (6, 'Agree very much'),
    ]

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(JobSatisfactionQuestion, related_name='answers', on_delete=models.CASCADE)
    response = models.IntegerField(choices=RESPONSE_CHOICES)
    response_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to {self.question.question_text}: {self.get_response_display()}"

class DemographicData(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female')
    ]
    
    AGE_GROUP_CHOICES = [
        ('20_below', '20yrs and below'),
        ('21_30', '21-30yrs'),
        ('31_40', '31-40yrs'),
        ('41_50', '41-50yrs'),
        ('51_60', '51-60yrs')
    ]
    
    EXPERIENCE_CHOICES = [
        ('5_below', '5yrs and below'),
        ('6_9', '6-9yrs'),
        ('10_19', '10-19yrs'),
        ('20_above', '20 and above')
    ]
    
    QUALIFICATION_CHOICES = [
        ('below_o', 'Below O’ level'),
        ('o_level', 'O’ level'),
        ('a_level', 'A’ level'),
        ('diploma', 'Diploma'),
        ('undergraduate', 'Undergraduate'),
        ('postgraduate', 'Post-graduate')
    ]
    
    DESIGNATION_CHOICES = [
        ('senior_management', 'Senior Management'),
        ('professional_employees', 'Professional Employees'),
        ('middle_management', 'Middle Management'),
        ('line_employees', 'Line Employees')
    ]
    
    CONTRACT_CHOICES = [
        ('fixed_term', 'Fixed –Term Contract'),
        ('permanent', 'Permanent Contract')
    ]
    DEPARTMENT_CHOICES = [
        ('HR', 'Human Resources'),
        ('IT', 'Information Technology'),
        ('FIN', 'Finance'),
        ('MKT', 'Marketing'),
        ('DEV', 'Development'),
    ]
    
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, default='male')
    age_group = models.CharField(max_length=10, choices=AGE_GROUP_CHOICES, default='20_below')
    work_experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES, default='5_below')
    highest_qualification = models.CharField(max_length=20, choices=QUALIFICATION_CHOICES, default='o_level')
    designation = models.CharField(max_length=30, choices=DESIGNATION_CHOICES, default='line_employees')
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, default='MKT')
    contract_type = models.CharField(max_length=15, choices=CONTRACT_CHOICES, default='permanent')
    response_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gender}, {self.age_group}, {self.designation}"



