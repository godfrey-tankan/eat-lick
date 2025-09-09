from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from .forms import *
import json
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from a_bot.views import get_text_message_input,send_message
from django.contrib.auth.decorators import login_required
from .models import *
from django.db.models import Count, Avg, OuterRef, Subquery,When, IntegerField, Case, Q
from .decorators import check_user_feedback
from django.utils.timezone import now


# Create your views here.
def home_view(request):
    if request.user.is_staff:
        return redirect('staff_dashboard')
    return render(request,'home.html')

@login_required
def staff_dashboard_view(request):
    if not request.user.is_staff:
        return HttpResponse('You are not authorized to view this page', status=403)

    # Update qualification mapping to match Homelink choices
    QUALIFICATION_VALUE_MAP = {
        'o_level': 1,
        'a_level': 2,
        'diploma': 3,
        'degree': 4,
        'post_grad': 5,
    }

    # Get total participants (users who have submitted answers)
    total_participants = LikertScaleAnswer.objects.values('user_id').distinct().count()

    # Calculate average feedback for each department
    department_feedback = DemographicData.objects.values('department').annotate(
        avg_feedback=Avg('user_id__likertscaleanswer__response')
    ).order_by('-avg_feedback')

    most_proper_department = department_feedback.first() if department_feedback else None

    # Calculate average qualification (convert text values to numeric scores)
    qualification_scores = {
        'o_level': 1,
        'a_level': 2, 
        'diploma': 3,
        'degree': 4,
        'post_grad': 5,
    }
    
    # Get all qualifications and convert to scores
    qualifications = DemographicData.objects.values_list('highest_qualification', flat=True)
    qualification_scores_list = [qualification_scores.get(q, 0) for q in qualifications if q in qualification_scores]
    
    # Calculate average
    average_qualification_score = sum(qualification_scores_list) / len(qualification_scores_list) if qualification_scores_list else 0
    
    # Convert back to text representation
    average_qualification_str = None
    if average_qualification_score is not None:
        # Find the closest qualification level
        rounded_score = round(average_qualification_score)
        average_qualification_str = next(
            (key for key, value in qualification_scores.items() if value == rounded_score),
            'o_level'  # default
        )

    # Determine critical department needing attention (lowest average feedback)
    critical_department = department_feedback.last() if department_feedback else None

    # Get the top 3 complaints (questions with lowest average scores)
    top_complaints = LikertScaleAnswer.objects.values('question__question_text').annotate(
        avg_score=Avg('response'),
        response_count=Count('id')
    ).filter(response_count__gte=3).order_by('avg_score')[:3]

    # Format complaints for display
    top_complaints_list = [f"{complaint['question__question_text'][:50]}... (Avg: {complaint['avg_score']:.1f})" 
                        for complaint in top_complaints]

    # Prepare data for charts - feedback distribution by department
    feedback_distribution_by_department = DemographicData.objects.values('department').annotate(
        total_responses=Count('user_id__likertscaleanswer'),
        positive_feedback=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__gte=4)),
        negative_feedback=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__lt=4))
    )

    # Average feedback by department
    average_feedback_by_department = DemographicData.objects.values('department').annotate(
        avg_feedback=Avg('user_id__likertscaleanswer__response')
    )

    # Prepare data for the template
    chart_data = {
        'feedback_distribution_by_department': list(feedback_distribution_by_department),
        'average_feedback_by_department': list(average_feedback_by_department),
    }

    # Pass the new context variables
    context = {
        'total_participants': total_participants,
        'most_proper_department': most_proper_department,
        'average_qualification': average_qualification_str,
        'critical_department': critical_department,
        'top_complaints': top_complaints_list,
        'chart_data': json.dumps(chart_data),  # Serialize to JSON for JavaScript
    }

    return render(request, 'staff/staff_dashboard.html', context)


# @login_required
def aggregated_feedback_view(request):
    if not request.user.is_staff:
        return HttpResponse('You are not authorized to view this page', status=403)
    
    # Get total responses count
    total_responses = LikertScaleAnswer.objects.count()
    
    # Get total number of participants (unique users)
    total_participants = LikertScaleAnswer.objects.values('user_id').distinct().count()

    question_summary = {}
    questions = JobSatisfactionQuestion.objects.all()

    for question in questions:
        responses = LikertScaleAnswer.objects.filter(question=question)
        count_responses = responses.count()
        
        if count_responses > 0:
            avg_response = responses.aggregate(Avg('response'))['response__avg']
            
            # For Yes/No questions, adjust the positive threshold
            if any(phrase in question.question_text.lower() for phrase in ['yes/no', 'have you', 'are you', 'is the', 'does the']):
                percentage_positive = responses.filter(response=1).count() / count_responses * 100
            else:
                # For Likert scale questions (1-6), consider 4-6 as positive
                percentage_positive = responses.filter(response__gte=4).count() / count_responses * 100
            # Calculate response distribution for better insights
            response_distribution = {}
            for i in range(1, 7):  # For Likert scale 1-6
                response_distribution[i] = responses.filter(response=i).count()
            
            question_summary[question] = {
                'average': avg_response,
                'percentage_positive': percentage_positive,
                'count': count_responses,
                'distribution': response_distribution
            }

    # Department feedback analysis - improved query
    departments_feedback = DemographicData.objects.values('department').annotate(
        total_employees=Count('user_id', distinct=True),
        avg_feedback=Avg('user_id__likertscaleanswer__response'),
        response_count=Count('user_id__likertscaleanswer'),
        positive_count=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__gte=4)),
        negative_count=Count('user_id__likertscaleanswer', filter=Q(user_id__likertscaleanswer__response__lte=3))
    ).filter(response_count__gt=0).order_by('avg_feedback')

    # Get worst and best departments
    worst_department = departments_feedback.first() if departments_feedback else None
    best_department = departments_feedback.last() if departments_feedback else None

    # Salary complaints - more accurate calculation
    # Get all pay-related questions
    pay_questions = JobSatisfactionQuestion.objects.filter(category='pay')
    salary_complaints = LikertScaleAnswer.objects.filter(
        question__in=pay_questions,
        response__lte=3  # Scores 1-3 are considered complaints
    ).count()
    # print("Salary complaints count:", salary_complaints)
    # print("Total pay-related responses:", LikertScaleAnswer.objects.filter(question__in=pay_questions).count())
    # print("percentage_positive:", question_summary)
    
    # Calculate salary satisfaction percentage
    total_pay_responses = LikertScaleAnswer.objects.filter(question__in=pay_questions).count()
    salary_satisfaction_percentage = 0
    if total_pay_responses > 0:
        positive_pay_responses = LikertScaleAnswer.objects.filter(
            question__in=pay_questions,
            response__gte=4
        ).count()
        salary_satisfaction_percentage = (positive_pay_responses / total_pay_responses) * 100

    # Get top concerns (questions with lowest average scores)
    top_concerns = []
    for question, summary in question_summary.items():
        if summary['count'] >= 5:  # Only include questions with sufficient responses
            top_concerns.append({
                'question': question,
                'average': summary['average'],
                'count': summary['count']
            })
    
    # Sort by average score (lowest first) and take top 5
    top_concerns = sorted(top_concerns, key=lambda x: x['average'])[:5]

    # Get overall satisfaction metrics
    overall_avg_score = LikertScaleAnswer.objects.aggregate(avg=Avg('response'))['avg'] or 0
    overall_positive_percentage = 0
    if total_responses > 0:
        overall_positive_responses = LikertScaleAnswer.objects.filter(response__gte=4).count()
        overall_positive_percentage = (overall_positive_responses / total_responses) * 100

    # Get response rate by department
    department_response_rates = []
    for dept in departments_feedback:
        total_employees_in_dept = DemographicData.objects.filter(
            department=dept['department']
        ).values('user_id').distinct().count()
        
        if total_employees_in_dept > 0:
            response_rate = (dept['response_count'] / total_employees_in_dept) * 100
            department_response_rates.append({
                'department': dept['department'],
                'response_rate': response_rate,
                'total_employees': total_employees_in_dept,
                'responses': dept['response_count']
            })

    context = {
        'total_responses': total_responses,
        'total_participants': total_participants,
        'question_summary': question_summary,
        'departments_feedback': list(departments_feedback),
        'worst_department': worst_department,
        'best_department': best_department,
        'salary_complaints': salary_complaints,
        'salary_satisfaction_percentage': salary_satisfaction_percentage,
        'total_pay_responses': total_pay_responses,
        'top_concerns': top_concerns,
        'overall_avg_score': overall_avg_score,
        'overall_positive_percentage': overall_positive_percentage,
        'department_response_rates': department_response_rates,
        'now': now()
    }

    return render(request, 'feedbacks/aggregated_feedback.html', context)

# @check_user_feedback
# @login_required
@csrf_exempt
def demographic_data_view(request):
    if request.method == 'POST':
        form = DemographicDataForm(request.POST)
        if form.is_valid():
            # Get the username from the POST data
            username = request.POST.get('username')
            print(f"Username from form: {username}")
            
            # Check if a user with this username exists
            user, created = User.objects.get_or_create(username=username)
            try:
                demographic_ob = DemographicData.objects.filter(user_id=user)
                if demographic_ob.exists():
                    print("User already submitted demographic data")
                    return render(request, 'review_submited.html')
            except Exception as e:
                print('Exception -> ', e)
            
            if created:
                # Set a default password or other attributes if necessary
                user.set_password(User.objects.make_random_password())
                user.save()
                print(f"Created new user: {user.username}")

            # Save demographic data
            demographic_data = form.save(commit=False)
            demographic_data.user_id = user  
            demographic_data.save()
            print('Saved demographic data successfully')
            return redirect('job_satisfaction')
        else:
            print("Form errors:", form.errors)
            print("Form data:", request.POST)
    else:
        form = DemographicDataForm()
    return render(request, 'demographic_data.html', {'form': form})

# @login_required
@csrf_exempt
def job_satisfaction_view(request):
    questions = JobSatisfactionQuestion.objects.all()

    if request.method == 'POST':
        form = JobSatisfactionForm(request.POST, questions=questions)
        print(f"Form is valid: {form.is_valid()}")
        
        if not form.is_valid():
            print("FORM ERRORS:", form.errors)
            print("POST DATA:", request.POST)
        
        if form.is_valid():
            username = request.POST.get('username')
            print(f"Username from job satisfaction form: {username}")
            
            try:
                user = User.objects.get(username=username)
                print(f"Found user: {user.username}")
                
                # Check if user already submitted answers
                demographic_ob = LikertScaleAnswer.objects.filter(user_id=user)
                if demographic_ob.exists():
                    print("User already submitted job satisfaction answers")
                    return render(request, 'review_submited.html')
                    
            except User.DoesNotExist:
                print(f"User {username} does not exist")
                return render(request, 'demographic_data.html', {'form': DemographicDataForm(), 'error': 'User not found. Please start over.'})
            except Exception as e:
                print('Exception -> ', e)
                
            # Process form data
            for field_name, response in form.cleaned_data.items():
                if field_name.startswith('question_'):
                    question_id = int(field_name.split('_')[1])
                    try:
                        question = JobSatisfactionQuestion.objects.get(id=question_id)
                        
                        if isinstance(response, str):  # Text field (open-ended)
                            LikertScaleAnswer.objects.create(
                                user_id=user,
                                question=question, 
                                response=0,
                                text_response=response 
                            )
                            print(f"Saved text response for question {question_id}")
                        else:
                            LikertScaleAnswer.objects.create(
                                user_id=user,
                                question=question, 
                                response=response
                            )
                            print(f"Saved response {response} for question {question_id}")
                    except JobSatisfactionQuestion.DoesNotExist:
                        print(f"Question with ID {question_id} does not exist")
                    except Exception as e:
                        print(f"Error saving answer for question {question_id}: {e}")
            
            print("All answers saved successfully, redirecting to thank you page")
            return redirect('thank_you') 
        else:
            # Form is not valid, re-render with errors
            print("Form validation failed")
    else:
        form = JobSatisfactionForm(questions=questions)
        print("GET request, rendering empty form")

    return render(request, 'job_satisfaction.html', {'form': form})

def thank_you(request):
    return render(request, 'thank_you.html')

@login_required
def feedback_details(request, user_id):
    if not request.user.is_staff:
        return HttpResponse('You are not authorized to view this page', status=403)

    user = get_object_or_404(User, id=user_id)
    feedbacks = LikertScaleAnswer.objects.filter(user_id=user).select_related('question')
    
    feedback_details = []
    RESPONSE_CHOICES = {
        6: 'Strongly Agree',
        5: 'Agree',
        4: "Don't Know",
        3: 'Disagree',
        2: 'Strongly Disagree',
    }

    for feedback in feedbacks:
        try:
            text_response_int = int(feedback.text_response)
        except (TypeError, ValueError):
            text_response_int = None
        if text_response_int :
            response_text = RESPONSE_CHOICES.get(text_response_int, 'No response')
        elif feedback.text_response =='0':
            response_text = "No"
        else:
            response_text = 'Yes' if feedback.text_response == '1' else feedback.text_response or 'No response'
        details = {
            'question_text': feedback.question.question_text,
            'response': feedback.response,
            'response_text': response_text,
            'response_date': feedback.response_date.strftime("%Y-%m-%d %H:%M")
        }
        feedback_details.append(details)

    return JsonResponse({'feedbacks': feedback_details})

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


