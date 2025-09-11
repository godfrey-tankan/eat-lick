from django import forms
from a_home.models import *
import re
from django.core.exceptions import ValidationError


class DemographicDataForm(forms.ModelForm):
    # Update choices to match Homelink's survey
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
        ('over_15', 'Over 15 years'),
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
        ('home_link_money_transfers', 'Homelink Money Transfers'),
        ('homelink_finance', 'Homelink Finance'),
        ('projects_and_mortgages', 'Projects And Mortgages'),
        ('finance_and_investments', 'Finance And Investments'),
        ('support_services', 'Support Services'),
        ('security', 'Security'),
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
        ('mutare_and_rusape', 'Mutare and Rusape'),
    ]
    
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.RadioSelect)
    age_group = forms.ChoiceField(choices=AGE_GROUP_CHOICES, widget=forms.Select)
    work_experience = forms.ChoiceField(choices=EXPERIENCE_CHOICES, widget=forms.Select, 
                                    label="Length of Continuous Service (in years)")
    highest_qualification = forms.ChoiceField(choices=QUALIFICATION_CHOICES, widget=forms.Select)
    designation = forms.ChoiceField(choices=DESIGNATION_CHOICES, widget=forms.Select)
    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES, widget=forms.Select)
    division = forms.ChoiceField(choices=DIVISION_CHOICES, widget=forms.Select, required=False)
    contract_type = forms.ChoiceField(choices=CONTRACT_CHOICES, widget=forms.RadioSelect)
    location = forms.ChoiceField(choices=LOCATION_CHOICES, widget=forms.Select, required=False)

    class Meta:
        model = DemographicData
        fields = [
            'gender', 'age_group', 'work_experience', 'highest_qualification', 
            'designation', 'department', 'division', 'contract_type', 'location'
        ]
        widgets = {
            'gender': forms.RadioSelect,
            'contract_type': forms.RadioSelect,
        }
        
    def __init__(self, *args, **kwargs):
        super(DemographicDataForm, self).__init__(*args, **kwargs)
        self.fields['gender'].choices = self.GENDER_CHOICES
        self.fields['age_group'].choices = self.AGE_GROUP_CHOICES
        self.fields['work_experience'].choices = self.EXPERIENCE_CHOICES
        self.fields['highest_qualification'].choices = self.QUALIFICATION_CHOICES
        self.fields['designation'].choices = self.DESIGNATION_CHOICES
        self.fields['department'].choices = self.DEPARTMENT_CHOICES
        self.fields['division'].choices = self.DIVISION_CHOICES
        self.fields['contract_type'].choices = self.CONTRACT_CHOICES
        self.fields['location'].choices = self.LOCATION_CHOICES
        
        for field in self.fields.values():
            field.required = True 
        self.fields['division'].required = False
        self.fields['location'].required = False


class JobSatisfactionForm(forms.Form):
    # Updated to match the 6-point scale from the document
    RESPONSE_CHOICES = [
        (1, 'Disagree very much'),
        (2, 'Disagree moderately'),
        (3, 'Disagree slightly'),
        (4, 'Agree slightly'),
        (5, 'Agree moderately'),
        (6, 'Agree very much'),
    ]

    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions')
        super().__init__(*args, **kwargs)

        for question in questions:
            field_name = f'question_{question.id}'
            
            # All questions use the 6-point Likert scale
            self.fields[field_name] = forms.ChoiceField(
                choices=self.RESPONSE_CHOICES,
                label=question.question_text,
                widget=forms.RadioSelect, 
                required=question.required,
                error_messages={'required': 'Please answer this question'}
            )