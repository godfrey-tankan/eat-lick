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


def download_all_responses(request):
    import csv
    import pandas as pd
    from django.http import HttpResponse
    from django.db.models import Prefetch
    from django.utils import timezone
    from a_home.models import (
        DemographicData,
        LikertScaleAnswer,
        JobSatisfactionQuestion,
    )

    # Get all demographic data with prefetched answers
    demographics = (
        DemographicData.objects.select_related("user_id")
        .prefetch_related(
            Prefetch(
                "user_id__likertscaleanswer_set",
                queryset=LikertScaleAnswer.objects.select_related("question"),
                to_attr="answers",
            )
        )
        .all()
    )

    # Create response with CSV content
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="homelink_all_responses_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'
    )

    # Get all questions organized by ALL categories
    categories_order = [
        "pay",
        "promotion",
        "supervision",
        "fringe_benefits",
        "contingent_rewards",
        "operating_conditions",
        "coworkers",
        "nature_of_work",
        "communication",
        "health_and_safety",
        "vigour_energy",
        "dedication",
        "absorption",
    ]

    # Get questions in the order they should appear
    questions_by_category = {}
    for category in categories_order:
        questions_by_category[category] = JobSatisfactionQuestion.objects.filter(
            category=category
        ).order_by("id")

    writer = csv.writer(response)

    # Write headers based on the Excel template structure
    headers = [
        "USER ID",
        "GENDER",
        "LOCATION",
        "QUALIFICATION",
        "DESIGNATION",
        "DEPARTMENT",
        "EXPERIENCE",
        "AGE",
    ]

    pay_questions = list(questions_by_category["pay"])
    headers.extend([f"PAY {i+1}" for i in range(len(pay_questions))])

    # Add PROMOTION section - main header and sub-columns
    promotion_questions = list(questions_by_category["promotion"])
    headers.extend([f"PROMOTION {i+1}" for i in range(len(promotion_questions))])

    supervision_questions = list(questions_by_category["supervision"])
    headers.extend([f"SUPERVISION {i+1}" for i in range(len(supervision_questions))])

    fringe_questions = list(questions_by_category["fringe_benefits"])
    headers.extend([f"FRINGE BENEFITS {i+1}" for i in range(len(fringe_questions))])

    # Add CONTIGENT REWARDS section - main header and sub-columns
    contingent_questions = list(questions_by_category["contingent_rewards"])
    headers.extend(
        [f"CONTIGENT REWARDS {i+1}" for i in range(len(contingent_questions))]
    )

    # Add OPERATING CONDITIONS section - main header and sub-columns
    operating_questions = list(questions_by_category["operating_conditions"])
    headers.extend(
        [f"OPERATING CONDITIONS {i+1}" for i in range(len(operating_questions))]
    )

    coworkers_questions = list(questions_by_category["coworkers"])
    headers.extend([f"CORE WORKERS {i+1}" for i in range(len(coworkers_questions))])

    # Add NATURE OF WORK section - main header and sub-columns
    nature_questions = list(questions_by_category["nature_of_work"])
    headers.extend([f"NATURE OF WORK {i+1}" for i in range(len(nature_questions))])

    # Add COMMUNICATION section - main header and sub-columns
    communication_questions = list(questions_by_category["communication"])
    headers.extend(
        [f"COMMUNICATION {i+1}" for i in range(len(communication_questions))]
    )

    # Add HEALTH AND SAFETY section - main header and sub-columns
    health_questions = list(questions_by_category["health_and_safety"])
    headers.extend([f"HEALTH AND SAFETY {i+1}" for i in range(len(health_questions))])

    # Add VIGOUR AND ENERGY section - main header and sub-columns
    vigour_questions = list(questions_by_category["vigour_energy"])
    headers.extend([f"VIGOUR AND ENERGY {i+1}" for i in range(len(vigour_questions))])

    # Add DEDICATION section - main header and sub-columns
    dedication_questions = list(questions_by_category["dedication"])
    headers.extend([f"DEDICATION {i+1}" for i in range(len(dedication_questions))])

    # Add ABSORPTION section - main header and sub-columns
    absorption_questions = list(questions_by_category["absorption"])
    headers.extend([f"ABSORPTION {i+1}" for i in range(len(absorption_questions))])

    # Write headers
    writer.writerow(headers)

    # Write data rows
    for demo in demographics:
        # Start with demographic data
        row = [
            demo.user_id.id,
            demo.get_gender_display(),
            demo.get_location_display() if demo.location else "",
            demo.get_highest_qualification_display(),
            demo.get_designation_display(),
            demo.get_department_display(),
            demo.get_work_experience_display(),
            demo.get_age_group_display(),
        ]

        # Helper function to get answer for a question
        def get_answer_value(question):
            for answer in getattr(demo.user_id, "answers", []):
                if answer.question_id == question.id:
                    return answer.response if answer.response else 0
            return 0

        # Add pay section - main column (empty) and answers
        for question in pay_questions:
            row.append(get_answer_value(question))

        # Add promotion section - main column (empty) and answers
        # row.append("")  # PROMOTTION main header column (empty)
        for question in promotion_questions:
            row.append(get_answer_value(question))

        # Add supervision section - main column (empty) and answers
        # row.append("")  # SUPERVISION main header column (empty)
        for question in supervision_questions:
            row.append(get_answer_value(question))

        # Add fringe benefits section - main column (empty) and answers
        # row.append("")  # FRINGE BENEFITS main header column (empty)
        for question in fringe_questions:
            row.append(get_answer_value(question))

        # Add contingent rewards section - main column (empty) and answers
        # row.append("")  # CONTIGENT REWARDS main header column (empty)
        for question in contingent_questions:
            row.append(get_answer_value(question))

        # Add operating conditions section - main column (empty) and answers
        # row.append("")  # OPERATING CONDITIONS main header column (empty)
        for question in operating_questions:
            row.append(get_answer_value(question))

        # Add core workers section - main column (empty) and answers
        # row.append("")  # CORE WORKERS main header column (empty)
        for question in coworkers_questions:
            row.append(get_answer_value(question))

        # Add nature of work section - main column (empty) and answers
        # row.append("")  # NATURE OF WORK main header column (empty)
        for question in nature_questions:
            row.append(get_answer_value(question))

        # Add communication section - main column (empty) and answers
        # row.append("")  # COMMUNICATION main header column (empty)
        for question in communication_questions:
            row.append(get_answer_value(question))

        # Add health and safety section - main column (empty) and answers
        # row.append("")  # HEALTH AND SAFETY main header column (empty)
        for question in health_questions:
            row.append(get_answer_value(question))

        # Add vigour and energy section - main column (empty) and answers
        # row.append("")  # VIGOUR AND ENERGY main header column (empty)
        for question in vigour_questions:
            row.append(get_answer_value(question))

        # Add dedication section - main column (empty) and answers
        # row.append("")  # DEDICATION main header column (empty)
        for question in dedication_questions:
            row.append(get_answer_value(question))

        # Add absorption section - main column (empty) and answers
        # row.append("")  # ABSORPTION main header column (empty)
        for question in absorption_questions:
            row.append(get_answer_value(question))

        writer.writerow(row)

    return response
