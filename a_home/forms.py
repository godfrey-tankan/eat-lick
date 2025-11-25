from django import forms
from .models import *


class CompanySelectionForm(forms.Form):
    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_active=True),
        empty_label="Select a company",
        widget=forms.Select(
            attrs={"class": "form-control", "style": "padding: 10px; font-size: 16px;"}
        ),
    )


class NHSDemographicForm(forms.ModelForm):
    CLIENT_TYPE_CHOICES = [
        ("airline_passenger", "AIRLINE (Passenger)"),
        ("airline_cargo", "AIRLINE (CARGO)"),
        ("travel_agent", "TRAVEL AGENT"),
        ("financial_institution", "FINANCIAL INSTITUTION"),
        ("government_department", "GOVERNMENT DEPARTMENT"),
        ("individual_traveller", "INDIVIDUAL TRAVELLER"),
        ("regulator", "REGULATOR"),
    ]

    client_type = forms.ChoiceField(
        choices=CLIENT_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label="Please select your category",
    )

    class Meta:
        model = DemographicData
        fields = ["client_type"]


class HITDemographicForm(forms.ModelForm):
    GENDER_CHOICES = [("male", "Male"), ("female", "Female")]

    AGE_GROUP_CHOICES = [
        ("20_below", "20 years and below"),
        ("21_30", "21-30 years"),
        ("31_40", "31-40 years"),
        ("41_50", "41-50 years"),
        ("51_60", "51-60 years"),
        ("61_above", "61 years and above"),
    ]

    EXPERIENCE_CHOICES = [
        ("less_1", "Less than 1 year"),
        ("1_5", "1 to 5 years"),
        ("5_10", "5 to 10 years"),
        ("10_20", "10 to 20 years"),
        ("20_30", "20 to 30 years"),
        ("30_above", "Over 30 years"),
    ]

    DEPARTMENT_CHOICES = [
        ("admissions", "Admissions"),
        ("quality_assurance", "Quality Assurance"),
        ("registrar", "Registrar"),
        ("student_records", "Student Records"),
        ("examinations_office", "Examinations Office"),
        ("finance", "Finance"),
        ("procurement", "Procurement Management Unit"),
        ("library", "Library"),
        ("icts", "ICTS"),
        ("infrastructure_estates", "Infrastructure & Estates"),
        ("student_affairs", "Student Affairs"),
        ("central_service", "Central Service"),
        ("catering_services", "Catering Services"),
        ("security", "Security"),
        ("human_resources", "Human Resources"),
        ("communication_international", "Communication & International Relations"),
        ("internal_audit", "Internal Audit"),
        ("food_processing", "Food Processing Technology"),
        ("biotechnology", "Biotechnology"),
        ("polymer_technology", "Polymer Technology"),
        ("industrial_manufacturing", "Industrial & Manufacturing Engineering"),
        ("electronic_engineering", "Electronic Engineering"),
        ("biomedical_engineering", "Biomedical Engineering"),
        ("materials_engineering", "Materials Engineering"),
        ("chemical_process", "Chemical And Process Systems Engineering"),
        ("pharmaceutical_technology", "Pharmaceutical Technology"),
        ("radiography", "Radiography"),
        ("financial_engineering", "Financial Engineering"),
        ("electronic_commerce", "Electronic Commerce"),
        ("forensic_accounting", "Forensic Accounting & Auditing"),
        ("computer_science", "Computer Science"),
        ("software_engineering", "Software Engineering"),
        ("information_security", "Information Security and Assurance"),
        ("information_technology", "Information Technology"),
        ("ttlcc", "TTLCC"),
        ("technology_centre", "Technology Centre"),
        ("technology_education", "Technology Education Centre"),
        ("technopreneurship", "Technopreneurship Development Centre"),
        (
            "environmental_management",
            "Environmental Management, Renewable Energy and Climate Change",
        ),
        ("artificial_intelligence", "Artificial Intelligence and Machine Learning"),
    ]

    CONTRACT_CHOICES = [
        ("permanent", "Permanent"),
        ("contract", "Contract"),
        ("relief", "Relief"),
        ("casual", "Casual"),
    ]

    DESIGNATION_CHOICES = [
        ("principal_officer", "Principal Officer (1-3a)"),
        ("senior_manager", "Senior Manager (3a,4a,5a)"),
        ("supervisor", "Supervisor (6a and 7a)"),
        ("non_managerial", "Non-managerial (8-16)"),
    ]

    QUALIFICATION_CHOICES = [
        ("zjc", "ZJC"),
        ("o_level", "O Level"),
        ("a_level", "A Level"),
        ("diploma", "Diploma/Professional Qualifications"),
        ("degree", "Degree"),
        ("post_grad", "Post Graduate"),
    ]

    CATEGORY_CHOICES = [
        ("academic", "Academic Staff"),
        ("non_academic", "Non Academic Staff"),
    ]

    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "radio-group"}),
        label="Gender",
    )

    age_group = forms.ChoiceField(
        choices=AGE_GROUP_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Age Profile",
    )

    work_experience = forms.ChoiceField(
        choices=EXPERIENCE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Length of Continuous Service (in years)",
    )

    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Department",
    )

    contract_type = forms.ChoiceField(
        choices=CONTRACT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "radio-group"}),
        label="Type of Employment Contract",
    )

    designation = forms.ChoiceField(
        choices=DESIGNATION_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Function",
    )

    highest_qualification = forms.ChoiceField(
        choices=QUALIFICATION_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Highest Education Level Attained",
    )

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "radio-group"}),
        label="Category",
    )

    class Meta:
        model = DemographicData
        fields = [
            "gender",
            "age_group",
            "work_experience",
            "department",
            "contract_type",
            "designation",
            "highest_qualification",
            "category",
        ]


class SurveyResponseForm(forms.Form):
    RESPONSE_CHOICES = [
        (1, "Strongly disagree"),
        (2, "Disagree"),
        (3, "Neutral"),
        (4, "Agree"),
        (5, "Strongly agree"),
    ]

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company")
        self.questions = kwargs.pop("questions")
        super().__init__(*args, **kwargs)

        current_category = None
        for question in self.questions:
            # Add category header if category changes
            if question.category != current_category:
                current_category = question.category
                # Create a header field (non-input)
                header_field_name = f"header_{question.category}"
                self.fields[header_field_name] = forms.CharField(
                    required=False,
                    widget=forms.TextInput(
                        attrs={
                            "class": "category-header",
                            "readonly": True,
                            "style": "border: none; background: transparent; font-weight: bold; font-size: 1.2em; margin-top: 20px;",
                        }
                    ),
                )
                self.initial[header_field_name] = self.get_category_display(
                    question.category
                )

            # Create question field
            field_name = f"question_{question.id}"
            self.fields[field_name] = forms.ChoiceField(
                choices=self.RESPONSE_CHOICES,
                label=question.question_text,
                widget=forms.RadioSelect(attrs={"class": "question-radio"}),
                required=question.required,
                error_messages={"required": "Please answer this question"},
            )

    def get_category_display(self, category):
        category_display_map = {
            "general_satisfaction": "GENERAL SATISFACTION WITH NHS SERVICE",
            "brand_awareness": "BRAND AWARENESS AND VISIBILITY",
            "service_quality": "SERVICE QUALITY",
            "pricing_value": "PRICING AND VALUE FOR MONEY",
            "vision_strategy": "VISION AND STRATEGIC DIRECTION OF HIT",
            "job_satisfaction": "JOB SATISFACTION",
            "leadership": "LEADERSHIP AND PEOPLE MANAGEMENT",
            "conditions_service": "CONDITIONS OF SERVICE, SAFETY, HEALTH AND ENVIRONMENT",
            "communication": "COMMUNICATION",
            "learning_development": "LEARNING DEVELOPMENT",
            "organizational_culture": "ORGANISATIONAL CULTURE/WORK CULTURE",
            "nature_work": "NATURE OF WORK",
            "vigour": "VIGOUR",
            "dedication": "DEDICATION",
            "absorption": "ABSORPTION",
        }
        return category_display_map.get(category, category.replace("_", " ").title())
