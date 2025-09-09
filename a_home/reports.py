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
        total_responses=Count('user_id', distinct=True),
        positive_feedback_count=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__gte=4)),
        negative_feedback_count=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__lt=4)),
    )
    report_data["feedback_by_department"] = list(feedback_by_department)

    # Fetching feedback data based on highest qualification
    feedback_by_qualification = DemographicData.objects.values('highest_qualification').annotate(
        total_responses=Count('user_id', distinct=True),
        positive_feedback_count=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__gte=4)),
        negative_feedback_count=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__lt=4)),
    )
    report_data["feedback_by_qualification"] = list(feedback_by_qualification)

    # Fetching feedback data based on age group
    feedback_by_age_group = DemographicData.objects.values('age_group').annotate(
        total_responses=Count('user_id', distinct=True),
        positive_feedback_count=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__gte=4)),
        negative_feedback_count=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__lt=4)),
    )
    report_data["feedback_by_age_group"] = list(feedback_by_age_group)

    # Fetching feedback data based on designation
    feedback_by_designation = DemographicData.objects.values('designation').annotate(
        total_responses=Count('user_id', distinct=True),
        positive_feedback_count=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__gte=4)),
        negative_feedback_count=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__lt=4)),
    )
    report_data["feedback_by_designation"] = list(feedback_by_designation)

    # Question-based analysis
    questions = JobSatisfactionQuestion.objects.prefetch_related('answers').annotate(
        response_counts=Count('answers'),
        positive_feedback_count=Count('answers', filter=Q(answers__response__gte=4)),
        negative_feedback_count=Count('answers', filter=Q(answers__response__lt=4)),
    )

    for question in questions:
        report_data["feedback_by_question"].append({
            "category": question.category,
            "question_text": question.question_text[:100] + "..." if len(question.question_text) > 100 else question.question_text,
            "response_counts": question.response_counts,
            "positive_feedback_count": question.positive_feedback_count,
            "negative_feedback_count": question.negative_feedback_count,
        })

    return render(request, 'staff/full_report.html', {'report_data': report_data, 'date': now()})
@csrf_exempt
def generate_department_report(request):
    if request.method == 'GET':
        department_name = request.GET.get('department')
        
        if not department_name:
            # Show department selection page
            departments = DemographicData.objects.values_list('department', flat=True).distinct()
            return render(request, 'reports/department_select.html', {'departments': departments})
        
        demographic_data = DemographicData.objects.filter(department=department_name)

        # Get department statistics
        department_stats = demographic_data.aggregate(
            total_employees=Count('user_id', distinct=True),
            avg_feedback=Avg('user_id__likertscaleanswer__response'),
            total_responses=Count('user_id__likertscaleanswer')
        )

        # Get question analysis for this department
        questions = JobSatisfactionQuestion.objects.annotate(
            dept_response_count=Count('answers', filter=Q(answers__user_id__demographicdata__department=department_name)),
            dept_avg_score=Avg('answers__response', filter=Q(answers__user_id__demographicdata__department=department_name))
        ).filter(dept_response_count__gt=0)

        context = {
            'department': department_name,
            'stats': department_stats,
            'questions': questions,
            'date': now()
        }

        return render(request, 'reports/department_report.html', context)
    
    return render(request, 'reports/error.html', {'error': 'Invalid request method'})

@csrf_exempt
def generate_designation_report(request):
    designation_stats = DemographicData.objects.values('designation').annotate(
        total_employees=Count('user_id', distinct=True),
        total_responses=Count('user_id__likertscaleanswer'),
        avg_feedback=Avg('user_id__likertscaleanswer__response')
    ).order_by('designation')
    
    context = {
        'designation_stats': designation_stats,
        'date': now()
    }
    
    return render(request, 'reports/designation_report.html', context)
@csrf_exempt
def generate_qualification_report(request):
    qualification_stats = DemographicData.objects.values('highest_qualification').annotate(
        total_employees=Count('user_id', distinct=True),
        total_responses=Count('user_id__likertscaleanswer'),
        avg_feedback=Avg('user_id__likertscaleanswer__response'),
        positive_feedback=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__gte=4)),
        negative_feedback=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__lt=4))
    ).order_by('highest_qualification')
    
    context = {
        'qualification_stats': qualification_stats,
        'date': now()
    }
    
    return render(request, 'reports/qualification_report.html', context)

@csrf_exempt
def generate_age_group_report(request):
    age_group_stats = DemographicData.objects.values('age_group').annotate(
        total_employees=Count('user_id', distinct=True),
        total_responses=Count('user_id__likertscaleanswer'),
        avg_feedback=Avg('user_id__likertscaleanswer__response'),
        positive_feedback=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__gte=4)),
        negative_feedback=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__lt=4))
    ).order_by('age_group')
    
    context = {
        'age_group_stats': age_group_stats,
        'date': now()
    }
    
    return render(request, 'reports/age_group_report.html', context)