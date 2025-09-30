# a_home/views.py
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from .forms import *
import json
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from a_bot.views import get_text_message_input, send_message
from django.contrib.auth.decorators import login_required
from .models import *
from django.db.models import (
    Count,
    Avg,
    OuterRef,
    Subquery,
    When,
    IntegerField,
    Case,
    Q,
    Prefetch,
)
from .decorators import check_user_feedback
from django.utils.timezone import now
import time


# Create your views here.
def home_view(request):
    if request.user.is_staff:
        return redirect("staff_dashboard")
    return render(request, "home.html")


@login_required
def staff_dashboard_view(request):
    if not request.user.is_staff:
        return HttpResponse("You are not authorized to view this page", status=403)

    # Update positive/negative thresholds for 6-point scale (4-6 positive, 1-3 negative)
    POSITIVE_THRESHOLD = 4
    NEGATIVE_THRESHOLD = 3

    # Get total participants
    total_participants = LikertScaleAnswer.objects.values("user_id").distinct().count()

    # Calculate average feedback for each department
    department_feedback = (
        DemographicData.objects.values("department")
        .annotate(avg_feedback=Avg("user_id__likertscaleanswer__response"))
        .order_by("-avg_feedback")
    )

    most_proper_department = (
        department_feedback.first() if department_feedback else None
    )
    critical_department = department_feedback.last() if department_feedback else None

    # Calculate average qualification
    qualification_scores = {
        "o_level": 1,
        "a_level": 2,
        "diploma": 3,
        "degree": 4,
        "post_grad": 5,
    }

    qualifications = DemographicData.objects.values_list(
        "highest_qualification", flat=True
    )
    qualification_scores_list = [
        qualification_scores.get(q, 0)
        for q in qualifications
        if q in qualification_scores
    ]
    average_qualification_score = (
        sum(qualification_scores_list) / len(qualification_scores_list)
        if qualification_scores_list
        else 0
    )

    average_qualification_str = None
    if average_qualification_score is not None:
        rounded_score = round(average_qualification_score)
        average_qualification_str = next(
            (
                key
                for key, value in qualification_scores.items()
                if value == rounded_score
            ),
            "o_level",
        )

    # Get top complaints
    top_complaints = (
        LikertScaleAnswer.objects.values("question__question_text")
        .annotate(avg_score=Avg("response"), response_count=Count("id"))
        .filter(response_count__gte=3)
        .order_by("avg_score")[:3]
    )

    top_complaints_list = [
        f"{complaint['question__question_text'][:50]}... (Avg: {complaint['avg_score']:.1f}/6)"
        for complaint in top_complaints
    ]

    # Prepare data for charts
    feedback_distribution_by_department = DemographicData.objects.values(
        "department"
    ).annotate(
        total_responses=Count("user_id__likertscaleanswer"),
        positive_feedback=Count(
            "user_id__likertscaleanswer",
            filter=Q(user_id__likertscaleanswer__response__gte=POSITIVE_THRESHOLD),
        ),
        negative_feedback=Count(
            "user_id__likertscaleanswer",
            filter=Q(user_id__likertscaleanswer__response__lte=NEGATIVE_THRESHOLD),
        ),
    )

    average_feedback_by_department = DemographicData.objects.values(
        "department"
    ).annotate(avg_feedback=Avg("user_id__likertscaleanswer__response"))

    chart_data = {
        "feedback_distribution_by_department": list(
            feedback_distribution_by_department
        ),
        "average_feedback_by_department": list(average_feedback_by_department),
    }

    context = {
        "total_participants": total_participants,
        "most_proper_department": most_proper_department,
        "average_qualification": average_qualification_str,
        "critical_department": critical_department,
        "top_complaints": top_complaints_list,
        "chart_data": json.dumps(chart_data),
    }

    return render(request, "staff/staff_dashboard.html", context)


# @login_required
def aggregated_feedback_view(request):
    if not request.user.is_staff:
        return HttpResponse("You are not authorized to view this page", status=403)

    start_time = time.time()

    # Update thresholds for 6-point scale
    POSITIVE_THRESHOLD = 4
    NEGATIVE_THRESHOLD = 3

    questions = JobSatisfactionQuestion.objects.prefetch_related(
        Prefetch(
            "answers", queryset=LikertScaleAnswer.objects.select_related("user_id")
        )
    )

    total_responses = LikertScaleAnswer.objects.count()
    total_participants = LikertScaleAnswer.objects.values("user_id").distinct().count()

    question_summary = {}

    # Precompute response distributions
    response_distributions = {}
    for i in range(1, 7):  # Changed to 1-6 range
        response_distributions[i] = (
            LikertScaleAnswer.objects.filter(response=i)
            .values("question")
            .annotate(count=Count("id"))
        )

    dist_dict = {}
    for i in range(1, 7):
        dist_dict[i] = {
            item["question"]: item["count"] for item in response_distributions[i]
        }

    question_avgs = LikertScaleAnswer.objects.values("question").annotate(
        avg_response=Avg("response"),
        total_count=Count("id"),
        positive_count=Count("id", filter=Q(response__gte=POSITIVE_THRESHOLD)),
        negative_count=Count("id", filter=Q(response__lte=NEGATIVE_THRESHOLD)),
    )

    avg_dict = {item["question"]: item for item in question_avgs}

    for question in questions:
        question_data = avg_dict.get(question.id)

        if question_data and question_data["total_count"] > 0:
            distribution = {}
            for i in range(1, 7):
                distribution[i] = dist_dict[i].get(question.id, 0)

            percentage_positive = (
                question_data["positive_count"] / question_data["total_count"]
            ) * 100

            question_summary[question] = {
                "average": question_data["avg_response"],
                "percentage_positive": percentage_positive,
                "count": question_data["total_count"],
                "distribution": distribution,
            }

    # Optimize department feedback analysis with new thresholds
    departments_feedback = (
        DemographicData.objects.values("department")
        .annotate(
            total_employees=Count("user_id", distinct=True),
            avg_feedback=Avg("user_id__likertscaleanswer__response"),
            response_count=Count("user_id__likertscaleanswer"),
            positive_count=Count(
                "user_id__likertscaleanswer",
                filter=Q(user_id__likertscaleanswer__response__gte=POSITIVE_THRESHOLD),
            ),
            negative_count=Count(
                "user_id__likertscaleanswer",
                filter=Q(user_id__likertscaleanswer__response__lte=NEGATIVE_THRESHOLD),
            ),
        )
        .filter(response_count__gt=0)
        .order_by("avg_feedback")
    )

    worst_department = departments_feedback.first()
    best_department = departments_feedback.last()

    # Update salary complaints calculation
    pay_data = LikertScaleAnswer.objects.filter(question__category="pay").aggregate(
        total=Count("id"),
        complaints=Count("id", filter=Q(response__lte=NEGATIVE_THRESHOLD)),
        positive=Count("id", filter=Q(response__gte=POSITIVE_THRESHOLD)),
    )

    salary_complaints = pay_data["complaints"] or 0
    total_pay_responses = pay_data["total"] or 0
    salary_satisfaction_percentage = (
        (pay_data["positive"] / total_pay_responses * 100)
        if total_pay_responses > 0
        else 0
    )

    # Top concerns
    top_concerns = []
    for question, summary in question_summary.items():
        if summary["count"] >= 5:
            top_concerns.append(
                {
                    "question": question,
                    "average": summary["average"],
                    "count": summary["count"],
                }
            )

    top_concerns = sorted(top_concerns, key=lambda x: x["average"])[:5]

    # Overall satisfaction metrics
    overall_stats = LikertScaleAnswer.objects.aggregate(
        avg_score=Avg("response"),
        total=Count("id"),
        positive=Count("id", filter=Q(response__gte=POSITIVE_THRESHOLD)),
    )

    overall_avg_score = overall_stats["avg_score"] or 0
    overall_positive_percentage = (
        (overall_stats["positive"] / overall_stats["total"] * 100)
        if overall_stats["total"] > 0
        else 0
    )

    # Department response rates
    department_response_rates = []
    for dept in departments_feedback:
        department_response_rates.append(
            {
                "department": dept["department"],
                "response_rate": (
                    (dept["response_count"] / dept["total_employees"] * 100)
                    if dept["total_employees"] > 0
                    else 0
                ),
                "total_employees": dept["total_employees"],
                "responses": dept["response_count"],
            }
        )

    end_time = time.time()

    context = {
        "total_responses": total_responses,
        "total_participants": total_participants,
        "question_summary": question_summary,
        "departments_feedback": list(departments_feedback),
        "worst_department": worst_department,
        "best_department": best_department,
        "salary_complaints": salary_complaints,
        "salary_satisfaction_percentage": salary_satisfaction_percentage,
        "total_pay_responses": total_pay_responses,
        "top_concerns": top_concerns,
        "overall_avg_score": overall_avg_score,
        "overall_positive_percentage": overall_positive_percentage,
        "department_response_rates": department_response_rates,
        "now": now(),
        "execution_time": end_time - start_time,
    }

    return render(request, "feedbacks/aggregated_feedback.html", context)


# @check_user_feedback
# @login_required
@csrf_exempt
def demographic_data_view(request):
    if request.method == "POST":
        form = DemographicDataForm(request.POST)
        if form.is_valid():
            # Get the username from the POST data
            username = request.POST.get("username")
            print(f"Username from form: {username}")

            # Check if a user with this username exists
            user, created = User.objects.get_or_create(username=username)
            try:
                demographic_ob = DemographicData.objects.filter(user_id=user)
                if demographic_ob.exists():
                    print("User already submitted demographic data")
                    return render(request, "review_submited.html")
            except Exception as e:
                print("Exception -> ", e)

            if created:
                # Set a default password or other attributes if necessary
                user.set_password(User.objects.make_random_password())
                user.save()
                print(f"Created new user: {user.username}")

            # Save demographic data
            demographic_data = form.save(commit=False)
            demographic_data.user_id = user
            demographic_data.save()
            print("Saved demographic data successfully")
            return redirect("job_satisfaction")
        else:
            print("Form errors:", form.errors)
            print("Form data:", request.POST)
    else:
        form = DemographicDataForm()
    return render(request, "demographic_data.html", {"form": form})


# @login_required
@csrf_exempt
def job_satisfaction_view(request):
    questions = JobSatisfactionQuestion.objects.all()

    if request.method == "POST":
        form = JobSatisfactionForm(request.POST, questions=questions)
        print(f"Form is valid: {form.is_valid()}")

        if not form.is_valid():
            print("FORM ERRORS:", form.errors)
            print("POST DATA:", request.POST)

        if form.is_valid():
            username = request.POST.get("username")
            print(f"Username from job satisfaction form: {username}")

            try:
                user = User.objects.get(username=username)
                print(f"Found user: {user.username}")

                # Check if user already submitted answers
                existing_answers = LikertScaleAnswer.objects.filter(user_id=user)
                if existing_answers.exists():
                    print("User already submitted job satisfaction answers")
                    return render(request, "review_submited.html")

            except User.DoesNotExist:
                print(f"User {username} does not exist")
                return render(
                    request,
                    "demographic_data.html",
                    {
                        "form": DemographicDataForm(),
                        "error": "User not found. Please start over.",
                    },
                )
            except Exception as e:
                print("Exception -> ", e)
                return render(
                    request,
                    "demographic_data.html",
                    {
                        "form": DemographicDataForm(),
                        "error": "An error occurred. Please try again.",
                    },
                )

            # Process form data
            for field_name, response in form.cleaned_data.items():
                if field_name.startswith("question_"):
                    question_id = int(field_name.split("_")[1])
                    try:
                        question = JobSatisfactionQuestion.objects.get(id=question_id)

                        # Save the response (all questions use the 6-point scale)
                        LikertScaleAnswer.objects.create(
                            user_id=user, question=question, response=response
                        )
                        print(f"Saved response {response} for question {question_id}")
                    except JobSatisfactionQuestion.DoesNotExist:
                        print(f"Question with ID {question_id} does not exist")
                    except Exception as e:
                        print(f"Error saving answer for question {question_id}: {e}")

            print("All answers saved successfully, redirecting to thank you page")
            return redirect("thank_you")
        else:
            # Form is not valid, re-render with errors
            print("Form validation failed")
    else:
        form = JobSatisfactionForm(questions=questions)
        print("GET request, rendering empty form")

    return render(request, "job_satisfaction.html", {"form": form})


def thank_you(request):
    return render(request, "thank_you.html")


@login_required
def feedback_details(request, user_id):
    if not request.user.is_staff:
        return HttpResponse("You are not authorized to view this page", status=403)

    user = get_object_or_404(User, id=user_id)
    feedbacks = LikertScaleAnswer.objects.filter(user_id=user).select_related(
        "question"
    )

    feedback_details = []
    # Updated response choices to match the 6-point scale
    RESPONSE_CHOICES = {
        1: "Disagree very much",
        2: "Disagree moderately",
        3: "Disagree slightly",
        4: "Agree slightly",
        5: "Agree moderately",
        6: "Agree very much",
    }

    for feedback in feedbacks:
        details = {
            "question_text": feedback.question.question_text,
            "response": feedback.response,
            "response_text": RESPONSE_CHOICES.get(feedback.response, "No response"),
            "response_date": feedback.response_date.strftime("%Y-%m-%d %H:%M"),
        }
        feedback_details.append(details)

    demographic = (
        DemographicData.objects.filter(user_id=user).order_by("-response_date").first()
    )

    user_info = {
        "id": user.id,
    }

    if demographic:
        user_info.update(
            {
                "gender": demographic.get_gender_display(),
                "location": demographic.get_location_display(),
                "qualification": demographic.get_highest_qualification_display(),
                "designation": demographic.get_designation_display(),
                "department": demographic.get_department_display(),
                "experience": demographic.get_work_experience_display(),
                "age": demographic.get_age_group_display(),
                "response_date": demographic.response_date.strftime("%b %d, %Y"),
            }
        )

    return JsonResponse({"user": user_info, "feedbacks": feedback_details})


def feedback_list(request):
    if request.user.is_staff:
        feedbacks = LikertScaleAnswer.objects.select_related("question").order_by(
            "-response_date"
        )[:3]
        return render(request, "feedbacks/feedback_list.html", {"feedbacks": feedbacks})
    return HttpResponse("You are not authorized to view this page", status=403)


def feedback_detail(request):
    if request.user.is_staff:
        users = User.objects.all()
        feedbacks = DemographicData.objects.filter(user_id__in=users).order_by(
            "-response_date"
        )
        return render(
            request, "feedbacks/feedback_detail.html", {"feedbacks": feedbacks}
        )
    return HttpResponse("You are not authorized to view this page", status=403)


def get_user_feedback(request, user_id):
    feedbacks = LikertScaleAnswer.objects.filter(user_id=user_id).select_related(
        "question"
    )
    feedback_details = [
        {
            "question_text": feedback.question.question_text,
            "response": feedback.get_response_display(),
            "response_date": feedback.response_date.strftime("%Y-%m-%d %H:%M"),
        }
        for feedback in feedbacks
    ]
    return JsonResponse({"feedbacks": feedback_details})
