from django.shortcuts import render
from django.http import JsonResponse
from .models import JobSatisfactionQuestion, LikertScaleAnswer, DemographicData
from django.db.models import Count, Avg,Count, Q
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def generate_full_report(request):
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
