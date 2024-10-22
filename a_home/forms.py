from django import forms
from a_home.models import *
import re
from django.core.exceptions import ValidationError


class DemographicDataForm(forms.ModelForm):
    class Meta:
        model = DemographicData
        fields = [
            'gender', 'age_group', 'work_experience', 'highest_qualification', 
            'designation', 'department', 'contract_type'
        ]
        widgets = {
            'gender': forms.RadioSelect,  
            'age_group': forms.Select,    
            'work_experience': forms.Select,
            'highest_qualification': forms.Select,
            'designation': forms.Select,
            'contract_type': forms.RadioSelect,  
        }
        def __init__(self, *args, **kwargs):
            super(DemographicDataForm, self).__init__(*args, **kwargs)
            for field in self.fields.values():
                field.required = True 
        

class JobSatisfactionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions')
        super().__init__(*args, **kwargs)

        for question in questions:
            self.fields[f'question_{question.id}'] = forms.ChoiceField(
                choices=LikertScaleAnswer.RESPONSE_CHOICES,
                label=question.question_text,
                widget=forms.RadioSelect, 
                required=question.required
            )