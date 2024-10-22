from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from .forms import *
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from a_bot.views import get_text_message_input,send_message
from django.contrib.auth.decorators import login_required
from .models import *
from django.db.models import Count, Avg, OuterRef, Subquery,When, IntegerField, Case
from .decorators import check_user_feedback


# Create your views here.
def home_view(request):
    if request.user.is_staff:
        return redirect('staff_dashboard')
    return render(request,'home.html')

from django.db.models import Subquery, OuterRef, Avg, Count, Case, When, IntegerField
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import LikertScaleAnswer, DemographicData

@login_required
def staff_dashboard_view(request):
    if not request.user.is_staff:
        return HttpResponse('You are not authorized to view this page', status=403)
    QUALIFICATION_VALUE_MAP = {
        'below_o': 0,
        'o_level': 1,
        'a_level': 2,
        'diploma': 3,
        'undergraduate': 4,
        'postgraduate': 5,
    }

    total_participants = LikertScaleAnswer.objects.values('user_id').distinct().count()

    # Calculate average feedback for each department
    department_feedback = DemographicData.objects.annotate(
        avg_feedback=Subquery(
            LikertScaleAnswer.objects.filter(user_id=OuterRef('user_id')).values('response').annotate(
                avg_response=Avg('response')
            ).values('avg_response')[:1]
        )
    ).values('department', 'avg_feedback').order_by('-avg_feedback')

    most_proper_department = department_feedback.first()

    # Calculate average qualification
    average_qualification = DemographicData.objects.aggregate(
        avg_qualification=Avg(
            Case(
                When(highest_qualification='below_o', then=0),
                When(highest_qualification='o_level', then=1),
                When(highest_qualification='a_level', then=2),
                When(highest_qualification='diploma', then=3),
                When(highest_qualification='undergraduate', then=4),
                When(highest_qualification='postgraduate', then=5),
                output_field=IntegerField(),
            )
        )
    )['avg_qualification']

    average_qualification_str = None
    if average_qualification is not None:
        average_qualification_str = next(
            (key for key, value in QUALIFICATION_VALUE_MAP.items() if value == int(round(average_qualification))),
            None
        )

    # Determine critical branch needing attention using LikertScaleAnswer directly
    critical_branch = DemographicData.objects.annotate(
        avg_feedback=Avg('user_id__likertscaleanswer__response')  # Adjusting the query to reflect proper relations
    ).order_by('avg_feedback').first()

    # Get the most top 3 complaints (assuming complaints are in a specific question)
    top_complaints = LikertScaleAnswer.objects.values('question__question_text').annotate(
        complaint_count=Count('id')
    ).order_by('-complaint_count')[:3]

    # Format complaints for display
    top_complaints_list = [complaint['question__question_text'] for complaint in top_complaints]

    # Pass the new context variables
    context = {
        'total_participants': total_participants,
        'most_proper_department': most_proper_department,
        'average_qualification': average_qualification_str,
        'critical_branch': critical_branch,
        'top_complaints': top_complaints_list,
    }

    return render(request, 'staff/staff_dashboard.html', context)


@login_required
def aggregated_feedback_view(request):
    if  not request.user.is_staff:
        return HttpResponse('You are not authorized to view this page', status=403)
    total_responses = LikertScaleAnswer.objects.count()

    question_summary = {}

    questions = JobSatisfactionQuestion.objects.all()

    for question in questions:
        responses = LikertScaleAnswer.objects.filter(question=question)
        count_responses = responses.count()
        
        if count_responses > 0:
            avg_response = responses.aggregate(Avg('response'))['response__avg']
            percentage_positive = responses.filter(response__gte=4).count() / count_responses * 100
            
            question_summary[question] = {
                'average': avg_response,
                'percentage_positive': percentage_positive,
                'count': count_responses
            }

    departments_feedback = DemographicData.objects.values('department').annotate(
        avg_feedback=Avg('likertscaleanswer__response')
    ).order_by('avg_feedback')

    worst_department = departments_feedback.first() if departments_feedback else None

    salary_complaints = LikertScaleAnswer.objects.filter(
        question__category='pay', 
        response__lte=3
    ).count()

    context = {
        'total_responses': total_responses,
        'question_summary': question_summary,
        'worst_department': worst_department,
        'salary_complaints': salary_complaints
    }

    return render(request, 'feedbacks/aggregated_feedback.html', context)

@check_user_feedback
@login_required
def demographic_data_view(request):
    if request.method == 'POST':
        form = DemographicDataForm(request.POST)
        if form.is_valid():
            demographic_data = form.save(commit=False)
            demographic_data.user_id = request.user
            demographic_data.save()
            return redirect('job_satisfaction')
    else:
        form = DemographicDataForm()
    return render(request, 'demographic_data.html', {'form': form})


@login_required
def job_satisfaction_view(request):
    questions = JobSatisfactionQuestion.objects.all()

    if request.method == 'POST':
        form = JobSatisfactionForm(request.POST, questions=questions)
        if form.is_valid():
            for field_name, response in form.cleaned_data.items():
                question_id = int(field_name.split('_')[1])
                question = JobSatisfactionQuestion.objects.get(id=question_id)
                LikertScaleAnswer.objects.create(user_id=request.user,question=question, response=response)
            return redirect('thank_you') 
    else:
        form = JobSatisfactionForm(questions=questions)

    return render(request, 'job_satisfaction.html', {'form': form})

def thank_you(request):
    return render(request, 'thank_you.html')

@login_required
def feedback_details(request, user_id):
    # Get all feedback entries for the specific user
    if request.user.is_staff:
        user = get_object_or_404(User, id=user_id)
        feedbacks = LikertScaleAnswer.objects.filter(user_id=user)

        feedback_details = []
        
        for feedback in feedbacks:
            details = {
                'question': feedback.question.question_text,
                'response': feedback.get_response_display(),
            }
            feedback_details.append(details)
    else:
        return HttpResponse('You are not authorized to view this page', status=403)

    # Check if the user has any feedback
    if feedback_details:
        return JsonResponse({'feedbacks': feedback_details})
    else:
        return JsonResponse({'feedbacks': []})  #

def feedback_list(request):
    if request.user.is_staff:
        feedbacks = LikertScaleAnswer.objects.select_related('question').order_by('-response_date')[:3]
        return render(request, 'feedbacks/feedback_list.html', {'feedbacks': feedbacks})
    return HttpResponse('You are not authorized to view this page', status=403)


def feedback_detail(request):
    if request.user.is_staff:
        users = User.objects.all()
        feedbacks = DemographicData.objects.filter(user_id__in=users).order_by('-response_date')
        return render(request, 'feedbacks/feedback_detail.html', {'feedbacks': feedbacks})
    return HttpResponse('You are not authorized to view this page', status=403)

def get_user_feedback(request, user_id):
    feedbacks = LikertScaleAnswer.objects.filter(user_id=user_id).select_related('question')
    feedback_details = [
        {
            'question_text': feedback.question.question_text,
            'response': feedback.get_response_display(),
            'response_date': feedback.response_date.strftime("%Y-%m-%d %H:%M")
        } for feedback in feedbacks
    ]
    return JsonResponse({'feedbacks': feedback_details})
