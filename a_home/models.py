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
        (6, 'Strongly Agree'),
        (5, 'Agree'),
        (4, "Don't Know"),
        (3, 'Disagree'),
        (2, 'Strongly Disagree'),
    ]
    
    YES_NO_CHOICES = [
        (1, 'Yes'),
        (0, 'No'),
    ]

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(JobSatisfactionQuestion, related_name='answers', on_delete=models.CASCADE)
    response = models.IntegerField(choices=RESPONSE_CHOICES, null=True, blank=True)
    text_response = models.TextField(blank=True, null=True) 
    response_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.text_response:
            return f"Answer to {self.question.question_text}: {self.text_response[:50]}..."
        return f"Answer to {self.question.question_text}: {self.get_response_display()}"

class DemographicData(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female')
    ]
    
    AGE_GROUP_CHOICES = [
        ('before_1966', 'Before 1966'),
        ('1966_1976', '1966-1976'),
        ('1977_1994', '1977-1994'),
        ('after_1994', 'After 1994'),
    ]
    
    EXPERIENCE_CHOICES = [
        ('less_than_1', 'Less than 1 year'),
        ('1_to_5', '1 to 5 years'),
        ('5_to_10', '5 to 10 years'),
        ('10_to_15', '10 to 15 years'),
    ]
    
    QUALIFICATION_CHOICES = [
        ('o_level', 'O Level'),
        ('a_level', 'A Level'),
        ('diploma', 'Diploma/Professional Qualifications'),
        ('degree', 'Degree'),
        ('post_grad', 'Post Graduate'),
    ]
    
    DESIGNATION_CHOICES = [
        ('director', 'Director'),
        ('manager', 'Manager'),
        ('assistant_manager', 'Assistant Manager'),
        ('non_managerial', 'Non-managerial'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('money_transfers', 'Money Transfers'),
        ('homelink_finance', 'Homelink Finance'),
        ('compliance', 'Compliance'),
        ('legal', 'Legal'),
        ('finance', 'Finance'),
        ('marketing', 'Marketing'),
        ('projects', 'Projects'),
        ('mortgages', 'Mortgages'),
        ('security', 'Security'),
        ('human_capital', 'Human Capital'),
        ('ict', 'ICT'),
    ]
    
    DIVISION_CHOICES = [
        ('homelink_finance', 'Homelink Finance'),
        ('money_transfers', 'Money Transfers'),
        ('head_office', 'Head Office'),
    ]
    
    CONTRACT_CHOICES = [
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('relief', 'Relief'),
    ]
    
    LOCATION_CHOICES = [
        ('harare', 'Harare'),
        ('kwekwe', 'Kwekwe'),
        ('gweru', 'Gweru'),
        ('bulawayo', 'Bulawayo'),
        ('masvingo', 'Masvingo'),
    ]
    
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, default='male')
    age_group = models.CharField(max_length=50, choices=AGE_GROUP_CHOICES, default='20_below')
    work_experience = models.CharField(max_length=50, choices=EXPERIENCE_CHOICES, default='5_below')
    highest_qualification = models.CharField(max_length=50, choices=QUALIFICATION_CHOICES, default='o_level')
    designation = models.CharField(max_length=50, choices=DESIGNATION_CHOICES, default='line_employees')
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, default='MKT')
    contract_type = models.CharField(max_length=50, choices=CONTRACT_CHOICES, default='permanent')
    response_date = models.DateTimeField(auto_now_add=True)
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES, blank=True, null=True)
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.gender}, {self.age_group}, {self.designation}"



