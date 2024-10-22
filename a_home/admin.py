from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(JobSatisfactionQuestion)
class JobSatisfactionQuestionAdmin(admin.ModelAdmin):
    list_display = ['id','question_text', 'category', 'required']
    list_display_links = ['id','question_text']
    list_filter = ['category', 'required']
    search_fields = ['question_text']
    
@admin.register(LikertScaleAnswer)
class LikertScaleAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'response', 'response_date']
    list_display_links = ['id', 'question']
    list_filter = ['response_date']
    search_fields = ['question__question_text']

@admin.register(DemographicData)
class DemographicAdmin(admin.ModelAdmin):
    list_display = ['id','gender', 'age_group', 'work_experience', 'highest_qualification', 'designation', 'department', 'contract_type']
    list_display_links = ['id','gender']
    list_filter =['gender','highest_qualification']
    

