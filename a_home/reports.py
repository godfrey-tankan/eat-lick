from django.shortcuts import render
from django.http import JsonResponse
from .models import JobSatisfactionQuestion, LikertScaleAnswer, DemographicData
from django.db.models import Count, Avg,Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
import datetime
def generate_full_report(request):
    report_data = {
        "feedback_by_department": [],
        "feedback_by_qualification": [],
        "feedback_by_age_group": [],
        "feedback_by_designation": [],
        "feedback_by_question": []
    }

    # Fetching feedback data based on department
    feedback_by_department = DemographicData.objects.values('department').annotate(
        total_responses=Count('user_id' ,distinct=True),
        positive_feedback_count=Count('user_id__likertscaleanswer__response', filter=Q(user_id__likertscaleanswer__response__in=[4, 5, 6])),
        negative_feedback_count=Count('user_id__likertscaleanswer__response', filter=Q(user_id__likertscaleanswer__response__in=[1, 2, 3])),
    )

    report_data["feedback_by_department"] = list(feedback_by_department)

    # Fetching feedback data based on highest qualification
    feedback_by_qualification = DemographicData.objects.values('highest_qualification').annotate(
        total_responses=Count('user_id', distinct=True),
        positive_feedback_count=Count('user_id__likertscaleanswer__response', filter=Q(user_id__likertscaleanswer__response__in=[4, 5, 6])),
        negative_feedback_count=Count('user_id__likertscaleanswer__response', filter=Q(user_id__likertscaleanswer__response__in=[1, 2, 3])),
    )

    report_data["feedback_by_qualification"] = list(feedback_by_qualification)

    # Fetching feedback data based on age group
    feedback_by_age_group = DemographicData.objects.values('age_group').annotate(
        total_responses=Count('user_id' ,distinct=True),
        positive_feedback_count=Count('user_id__likertscaleanswer__response', filter=Q(user_id__likertscaleanswer__response__in=[4, 5, 6])),
        negative_feedback_count=Count('user_id__likertscaleanswer__response', filter=Q(user_id__likertscaleanswer__response__in=[1, 2, 3])),
    )

    report_data["feedback_by_age_group"] = list(feedback_by_age_group)

    # Fetching feedback data based on designation
    feedback_by_designation = DemographicData.objects.values('designation').annotate(
        total_responses=Count('user_id' ,distinct=True),
        positive_feedback_count=Count('user_id__likertscaleanswer__response', filter=Q(user_id__likertscaleanswer__response__in=[4, 5, 6])),
        negative_feedback_count=Count('user_id__likertscaleanswer__response', filter=Q(user_id__likertscaleanswer__response__in=[1, 2, 3])),
    )

    report_data["feedback_by_designation"] = list(feedback_by_designation)
    questions = JobSatisfactionQuestion.objects.prefetch_related('answers').annotate(
        response_counts=Count('answers'),
        positive_feedback_count=Count('answers', filter=Q(answers__response__in=[4, 5, 6])),
        negative_feedback_count=Count('answers', filter=Q(answers__response__in=[1, 2, 3])),
    )

    for question in questions:
        report_data["feedback_by_question"].append({
            "category": question.category,
            "question_text": question.question_text,
            "response_counts": question.response_counts,
            "positive_feedback_count": question.positive_feedback_count,
            "negative_feedback_count": question.negative_feedback_count,
        })

    return render(request, 'staff/full_report.html', {'report_data': report_data, 'date': now()})
@csrf_exempt
def generate_department_report(request):
    
    if request.method == 'POST':
        department_name = request.POST.get('department')

        demographic_data = DemographicData.objects.filter(department=department_name)

        feedback_by_department = demographic_data.values('department').annotate(
            total_responses=Count('user_id')
        )
        
        question_response_counts = []

        questions = JobSatisfactionQuestion.objects.all()
        for question in questions:
            response_counts = (
                LikertScaleAnswer.objects
                .filter(question=question, user_id__in=demographic_data.values('user_id'))  # Filter based on demographic data
                .values('response')  # Get the response values
                .annotate(count=Count('response'))  # Count each response
            )

            response_dict = {response[0]: response[1] for response in response_counts}  # Map response value to count
            question_response_counts.append({
                'question': question.question_text,
                'response_counts': response_dict,
            })

        report_data = {
            'feedback_by_department': list(feedback_by_department),
            'question_response_counts': question_response_counts,  # Add response counts to report data
        }

        return JsonResponse(report_data, safe=False)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def generate_designation_report(request):
    feedback_by_designation = DemographicData.objects.values('designation').annotate(
        total_responses=Count('user_id')
    )
    
    report_data = {
        'feedback_by_designation': list(feedback_by_designation),
    }
    
    return JsonResponse(report_data, safe=False)

@csrf_exempt
def generate_qualification_report(request):
    feedback_by_qualification = DemographicData.objects.values('highest_qualification').annotate(
        total_responses=Count('user_id')
    )
    report_data = {
        'feedback_by_qualification': list(feedback_by_qualification),
    }
    return JsonResponse(report_data, safe=False)

@csrf_exempt
def generate_age_group_report(request):
    feedback_by_age_group = DemographicData.objects.values('age_group').annotate(
        total_responses=Count('user_id')
    )
    
    report_data = {
        'feedback_by_age_group': list(feedback_by_age_group),
    }
    
    return JsonResponse(report_data, safe=False)
