from django.shortcuts import render
from django.http import JsonResponse
from .models import JobSatisfactionQuestion, LikertScaleAnswer, DemographicData
from django.db.models import Count, Avg

def generate_full_report(request):
    print('hit...................')
    feedback_by_department = DemographicData.objects.values('department').annotate(
        total_responses=Count('user_id')
    )
    feedback_by_qualification = DemographicData.objects.values('highest_qualification').annotate(
        total_responses=Count('user_id')
    )

    feedback_by_age_group = DemographicData.objects.values('age_group').annotate(
        total_responses=Count('user_id')
    )

    feedback_by_designation = DemographicData.objects.values('designation').annotate(
        total_responses=Count('user_id')
    )

    feedback_by_question = JobSatisfactionQuestion.objects.values('category', 'question_text').annotate(
        response_counts=Count('answers'),
        avg_response=Avg('answers__response')
    )
    report_data = {
        'feedback_by_department': list(feedback_by_department),
        'feedback_by_qualification': list(feedback_by_qualification),
        'feedback_by_age_group': list(feedback_by_age_group),
        'feedback_by_designation': list(feedback_by_designation),
        'feedback_by_question': list(feedback_by_question),
    }
    print('report_data -> ', report_data)

    return JsonResponse(report_data, safe=False)
