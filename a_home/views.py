# a_home/views.py
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from requests import request
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
from datetime import datetime, timedelta
import csv
import time

import uuid


def home_view(request):
    """Home page with company selection"""
    if request.method == "POST":
        form = CompanySelectionForm(request.POST)
        if form.is_valid():
            company = form.cleaned_data["company"]
            request.session["selected_company"] = company.id
            return redirect("demographic_data")
    else:
        form = CompanySelectionForm()

    companies = Company.objects.filter(is_active=True)
    return render(request, "home.html", {"form": form, "companies": companies})


def demographic_data_view(request):
    """Demographic data collection based on selected company"""
    # Check for company code in query parameters first, then POST data
    company_code = None
    company = None
    # Check query parameters
    if "company" in request.GET:
        company_code = request.GET.get("company", "x").upper()

    # Check POST data (for form submissions from home page)
    elif request.method == "POST" and "company" in request.POST:
        company_code = request.POST.get("company")

    # If we have a company code, process it
    if company_code:
        company = Company.objects.get(code=company_code.upper())

        try:

            # Initialize the appropriate form for GET display
            form = (
                NHSDemographicForm() if company.code == "NHS" else HITDemographicForm()
            )
            return render(
                request, "demographic_data.html", {"form": form, "company": company}
            )

        except Company.DoesNotExist:
            return redirect("home")

    # Handle demographic form submission (when user submits the actual demographic form)
    company_id = request.POST.get("company_id")
    if not company_id:
        return redirect("home")

    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":
        form = (
            NHSDemographicForm(request.POST)
            if company.code == "NHS"
            else HITDemographicForm(request.POST)
        )
        if form.is_valid():
            demographic_data = form.save(commit=False)
            demographic_data.company = company
            user_session_id = request.POST.get("user_session_id")
            if user_session_id:
                demographic_data.user_id = user_session_id
                print(f"Using user ID from localStorage: {user_session_id}")
            else:
                # Fallback: generate new ID (shouldn't happen with our frontend)
                demographic_data.user_id = str(uuid.uuid4())
                print("Generated new user ID as fallback")
            if not DemographicData.objects.filter(
                user_id=demographic_data.user_id, company=company
            ):
                demographic_data.save()
            return redirect(
                f"/surveys/survey/?company_id={company.id}&user_id={user_session_id}"
            )
        else:
            print("Form is invalid")
    elif company.code == "NHS":
        form = NHSDemographicForm()
    else:
        form = HITDemographicForm()

    return render(request, "demographic_data.html", {"form": form, "company": company})


def survey_questions_view(request):
    """Survey questions based on selected company"""
    company_id = request.GET.get("company_id")
    user_id = request.GET.get("user_id")
    if not company_id:
        return redirect("home")

    company = get_object_or_404(Company, id=company_id)
    questions = SurveyQuestion.objects.filter(company=company).order_by("order")

    # Check if user already completed survey
    existing_responses = SurveyResponse.objects.filter(user_id=user_id, company=company)
    if existing_responses.exists():
        return render(request, "review_submitted.html")

    if request.method == "POST":

        form = SurveyResponseForm(request.POST, company=company, questions=questions)
        if form.is_valid():
            for field_name, response in form.cleaned_data.items():
                if field_name.startswith("question_"):
                    question_id = int(field_name.split("_")[1])
                    question = SurveyQuestion.objects.get(id=question_id)

                    SurveyResponse.objects.create(
                        user_id=user_id,
                        company=company,
                        question=question,
                        response=response,
                    )

            return redirect("thank_you")
    else:
        form = SurveyResponseForm(company=company, questions=questions)

    return render(
        request,
        "survey_questions.html",
        {"form": form, "company": company, "questions": questions},
    )


@login_required
def company_dashboard_view(request):
    """Enhanced Company Dashboard with comprehensive analytics"""
    if not hasattr(request.user, "companyadmin"):
        return HttpResponse("You are not authorized to view this page", status=403)

    company_admin = request.user.companyadmin
    company = company_admin.company

    # Dashboard statistics
    total_responses = (
        SurveyResponse.objects.filter(company=company)
        .values("user_id")
        .distinct()
        .count()
    )

    # Average scores by category
    category_scores = (
        SurveyResponse.objects.filter(company=company)
        .values("question__category")
        .annotate(
            avg_score=Avg("response"),
            response_count=Count("id"),
            total_respondents=Count("user_id", distinct=True),
        )
        .order_by("-avg_score")
    )

    # Recent responses (last 7 days)
    recent_responses_count = SurveyResponse.objects.filter(
        company=company, response_date__gte=now() - timedelta(days=7)
    ).count()

    # Calculate completion rate
    total_questions = SurveyQuestion.objects.filter(company=company).count()
    total_possible_responses = (
        total_responses * total_questions if total_responses > 0 else 0
    )
    actual_responses = SurveyResponse.objects.filter(company=company).count()
    completion_rate = (
        (actual_responses / total_possible_responses * 100)
        if total_possible_responses > 0
        else 0
    )

    # Department performance (for HIT)
    if company.code == "HIT":
        department_scores = (
            DemographicData.objects.filter(company=company, department__isnull=False)
            .annotate(
                avg_score=Avg(
                    SurveyResponse.objects.filter(
                        company=company, user_id=models.OuterRef("user_id")
                    ).values("response")
                ),
                response_count=Count(
                    SurveyResponse.objects.filter(
                        company=company, user_id=models.OuterRef("user_id")
                    ).values("id")
                ),
            )
            .values("department", "avg_score", "response_count")
        )
    else:
        department_scores = []

    # Response trend (last 30 days)
    response_trend = (
        SurveyResponse.objects.filter(
            company=company, response_date__gte=now() - timedelta(days=30)
        )
        .extra({"date": "date(response_date)"})
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    # Top performing questions
    top_questions = (
        SurveyResponse.objects.filter(company=company)
        .values("question__question_text", "question__category")
        .annotate(avg_score=Avg("response"))
        .order_by("-avg_score")[:5]
    )

    # Areas needing improvement
    improvement_areas = (
        SurveyResponse.objects.filter(company=company)
        .values("question__question_text", "question__category")
        .annotate(avg_score=Avg("response"))
        .order_by("avg_score")[:5]
    )

    # Demographic insights
    demographic_breakdown = {
        "gender": DemographicData.objects.filter(company=company)
        .values("gender")
        .annotate(count=Count("id")),
        "age_group": DemographicData.objects.filter(company=company)
        .values("age_group")
        .annotate(count=Count("id")),
        "department": DemographicData.objects.filter(company=company)
        .values("department")
        .annotate(count=Count("id")),
    }

    context = {
        "company": company,
        "total_responses": total_responses,
        "category_scores": category_scores,
        "recent_responses_count": recent_responses_count,
        "completion_rate": round(completion_rate, 1),
        "department_scores": department_scores,
        "response_trend": list(response_trend),
        "top_questions": top_questions,
        "improvement_areas": improvement_areas,
        "demographic_breakdown": demographic_breakdown,
    }

    return render(request, "company_dashboard.html", context)


###############################################OLD VIEWS#####################################################


def thank_you(request):
    return render(request, "thank_you.html")


def review_submitted(request):
    return render(request, "review_submitted.html")


@login_required
def company_reports_view(request):
    """Detailed reports for company admins"""
    if not hasattr(request.user, "companyadmin"):
        return HttpResponse("You are not authorized to view this page", status=403)

    company_admin = request.user.companyadmin
    company = company_admin.company

    # Comprehensive report data
    questions = SurveyQuestion.objects.filter(company=company)
    question_stats = []

    for question in questions:
        responses = SurveyResponse.objects.filter(question=question)
        stats = responses.aggregate(
            avg_response=Avg("response"),
            total_responses=Count("id"),
            strongly_agree=Count("id", filter=Q(response=5)),
            agree=Count("id", filter=Q(response=4)),
            neutral=Count("id", filter=Q(response=3)),
            disagree=Count("id", filter=Q(response=2)),
            strongly_disagree=Count("id", filter=Q(response=1)),
        )

        # Calculate percentages
        total = stats["total_responses"]
        if total > 0:
            stats["strongly_agree_pct"] = (stats["strongly_agree"] / total) * 100
            stats["agree_pct"] = (stats["agree"] / total) * 100
            stats["neutral_pct"] = (stats["neutral"] / total) * 100
            stats["disagree_pct"] = (stats["disagree"] / total) * 100
            stats["strongly_disagree_pct"] = (stats["strongly_disagree"] / total) * 100
        else:
            stats.update(
                {
                    f"{key}_pct": 0
                    for key in [
                        "strongly_agree",
                        "agree",
                        "neutral",
                        "disagree",
                        "strongly_disagree",
                    ]
                }
            )

        question_stats.append({"question": question, "stats": stats})

    # Demographic breakdown
    demographics = DemographicData.objects.filter(company=company)

    # Response rate by demographic
    demographic_response_rates = {}
    for field in ["gender", "age_group", "department", "contract_type"]:
        if company.code == "HIT":  # Only for HIT
            demographic_response_rates[field] = (
                demographics.values(field)
                .annotate(count=Count("id"))
                .order_by("-count")
            )
        else:  # For NHS
            demographic_response_rates["client_type"] = (
                demographics.values("client_type")
                .annotate(count=Count("id"))
                .order_by("-count")
            )
            break  # Only client_type for NHS

    context = {
        "company": company,
        "question_stats": question_stats,
        "demographics": demographics,
        "demographic_response_rates": demographic_response_rates,
    }

    return render(request, "company_reports.html", context)


@login_required
def response_detail_view(request, user_id):
    """View individual response details"""
    if not hasattr(request.user, "companyadmin"):
        return HttpResponse("You are not authorized to view this page", status=403)

    company_admin = request.user.companyadmin
    company = company_admin.company

    # Get demographic data
    demographic_data = get_object_or_404(
        DemographicData, user_id=user_id, company=company
    )

    # Get survey responses
    survey_responses = SurveyResponse.objects.filter(
        user_id=user_id, company=company
    ).select_related("question")

    # Calculate average score
    avg_score = survey_responses.aggregate(avg=Avg("response"))["avg"]

    context = {
        "company": company,
        "demographic_data": demographic_data,
        "survey_responses": survey_responses,
        "avg_score": round(avg_score, 2) if avg_score else 0,
    }

    return render(request, "response_detail.html", context)


@login_required
def dexport_responses_csv(request):
    """Export all responses as CSV"""
    if not hasattr(request.user, "companyadmin"):
        return HttpResponse("You are not authorized to view this page", status=403)

    company_admin = request.user.companyadmin
    company = company_admin.company

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="{company.code}_survey_responses_{datetime.now().strftime("%Y%m%d")}.csv"'
    )

    writer = csv.writer(response)

    # Write headers
    headers = ["User ID", "Response Date"]

    # Add demographic fields based on company
    if company.code == "HIT":
        headers.extend(
            [
                "Gender",
                "Age Group",
                "Department",
                "Contract Type",
                "Designation",
                "Highest Qualification",
                "Category",
            ]
        )
    else:  # NHS
        headers.extend(["Client Type"])

    # Add questions
    questions = SurveyQuestion.objects.filter(company=company).order_by("order")
    for question in questions:
        headers.append(question.question_text[:50])  # Truncate long questions

    writer.writerow(headers)

    # Get all unique users
    user_ids = (
        SurveyResponse.objects.filter(company=company)
        .values_list("user_id", flat=True)
        .distinct()
    )

    for user_id in user_ids:
        try:
            demographic = DemographicData.objects.filter(
                user_id=user_id, company=company
            ).first()
            if not demographic:
                continue
            responses = SurveyResponse.objects.filter(user_id=user_id, company=company)

            row = [user_id, demographic.response_date.strftime("%Y-%m-%d %H:%M:%S")]

            # Add demographic data
            if company.code == "HIT":
                row.extend(
                    [
                        demographic.gender,
                        demographic.age_group,
                        demographic.department,
                        demographic.contract_type,
                        demographic.designation,
                        demographic.highest_qualification,
                        demographic.category,
                    ]
                )
            else:
                row.extend([demographic.client_type])

            # Add responses
            response_dict = {resp.question_id: resp.response for resp in responses}
            for question in questions:
                row.append(response_dict.get(question.id, ""))

            writer.writerow(row)
        except DemographicData.DoesNotExist:
            continue

    return response


@login_required
def export_responses_csv(request):
    """Export all responses as CSV"""
    if not hasattr(request.user, "companyadmin"):
        return HttpResponse("You are not authorized to view this page", status=403)

    company_admin = request.user.companyadmin
    company = company_admin.company

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="{company.code}_survey_responses_{datetime.now().strftime("%Y%m%d")}.csv"'
    )

    writer = csv.writer(response)

    # Use HIT template if company is HIT, otherwise use existing logic
    if company.code == "HIT":
        # Build headers based on actual question categories and counts from the questionnaire
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

        # PAY section (1 question)
        headers.extend(["PAY", "", ""])  # 3 columns for PAY

        # VISION AND STRATEGY (5 questions)
        headers.extend(["VISION AND STRATEGY"] + [""] * 4)  # 5 columns

        # JOB SATISFACTION (7 questions)
        headers.extend(["JOB SATISFACTION"] + [""] * 6)  # 7 columns

        # LEADERSHIP AND PEOPLE MANAGEMENT (6 questions)
        headers.extend(["LEADERSHIP AND PEOPLE MANAGEMENT"] + [""] * 5)  # 6 columns

        # CONDITIONS OF SERVICE (8 questions)
        headers.extend(["CONDITIONS OF SERVICE"] + [""] * 7)  # 8 columns

        # COMMUNICATION (6 questions)
        headers.extend(["COMMUNICATION"] + [""] * 5)  # 6 columns

        # LEARNING DEVELOPMENT (3 questions)
        headers.extend(["LEARNING DEVELOPMENT"] + [""] * 2)  # 3 columns

        # ORGANIZATIONAL CULTURE (3 questions)
        headers.extend(["ORGANIZATIONAL CULTURE"] + [""] * 2)  # 3 columns

        # NATURE OF WORK (3 questions)
        headers.extend(["NATURE OF WORK"] + [""] * 2)  # 3 columns

        # VIGOUR (3 questions)
        headers.extend(["VIGOUR"] + [""] * 2)  # 3 columns

        # DEDICATION (3 questions)
        headers.extend(["DEDICATION"] + [""] * 2)  # 3 columns

        # ABSORPTION (3 questions)
        headers.extend(["ABSORPTION"] + [""] * 2)  # 3 columns

        writer.writerow(headers)

        # Get all unique users
        user_ids = (
            SurveyResponse.objects.filter(company=company)
            .values_list("user_id", flat=True)
            .distinct()
        )

        # Pre-fetch all questions for HIT company and organize by category
        hit_questions = SurveyQuestion.objects.filter(company=company).order_by("order")
        questions_by_category = {}
        for question in hit_questions:
            if question.category not in questions_by_category:
                questions_by_category[question.category] = []
            questions_by_category[question.category].append(question)

        # Define the exact order and count of questions per category based on the questionnaire
        category_mapping = {
            "vision_strategy": ("VISION AND STRATEGY", 5),
            "job_satisfaction": ("JOB SATISFACTION", 7),
            "leadership": ("LEADERSHIP AND PEOPLE MANAGEMENT", 6),
            "conditions_service": ("CONDITIONS OF SERVICE", 8),
            "communication": ("COMMUNICATION", 6),
            "learning_development": ("LEARNING DEVELOPMENT", 3),
            "organizational_culture": ("ORGANIZATIONAL CULTURE", 3),
            "nature_work": ("NATURE OF WORK", 3),
            "vigour": ("VIGOUR", 3),
            "dedication": ("DEDICATION", 3),
            "absorption": ("ABSORPTION", 3),
        }

        for user_id in user_ids:
            try:
                demographic = DemographicData.objects.filter(
                    user_id=user_id, company=company
                ).first()
                if not demographic:
                    continue

                # Get all responses for this user
                responses = SurveyResponse.objects.filter(
                    user_id=user_id, company=company
                )
                response_dict = {resp.question_id: resp.response for resp in responses}

                # Start building the row with demographic data
                row = [
                    user_id,  # USER ID
                    demographic.gender or "",  # GENDER
                    "",  # LOCATION - not in demographic model
                    demographic.highest_qualification or "",  # QUALIFICATION
                    demographic.designation or "",  # DESIGNATION
                    demographic.department or "",  # DEPARTMENT
                    demographic.work_experience or "",  # EXPERIENCE
                    demographic.age_group or "",  # AGE
                ]

                # PAY section (question 7 from job satisfaction)
                pay_question = None
                job_satisfaction_questions = questions_by_category.get(
                    "job_satisfaction", []
                )
                if (
                    len(job_satisfaction_questions) >= 4
                ):  # Question 7 is the 4th in job satisfaction
                    pay_question = job_satisfaction_questions[3]
                pay_response = (
                    response_dict.get(pay_question.id, "") if pay_question else ""
                )
                row.extend([pay_response, "", ""])  # PAY with 2 empty columns

                # Add responses for each category in the exact order
                for category_key, (
                    header_name,
                    question_count,
                ) in category_mapping.items():
                    questions = questions_by_category.get(category_key, [])
                    # Get responses for available questions
                    for i in range(question_count):
                        if i < len(questions):
                            question = questions[i]
                            response_value = response_dict.get(question.id, "")
                            row.append(response_value)
                        else:
                            row.append("")  # Empty if no question

                writer.writerow(row)

            except DemographicData.DoesNotExist:
                continue

    else:  # NHS and other companies use existing logic
        # Write headers
        headers = ["User ID", "Response Date"]

        # Add demographic fields based on company
        if company.code == "NHS":  # Explicitly check for NHS
            headers.extend(["Client Type"])
        else:  # Other companies
            headers.extend([])  # Add appropriate headers for other companies

        # Add questions
        questions = SurveyQuestion.objects.filter(company=company).order_by("order")
        for question in questions:
            headers.append(question.question_text[:50])  # Truncate long questions

        writer.writerow(headers)

        # Get all unique users
        user_ids = (
            SurveyResponse.objects.filter(company=company)
            .values_list("user_id", flat=True)
            .distinct()
        )

        for user_id in user_ids:
            try:
                demographic = DemographicData.objects.filter(
                    user_id=user_id, company=company
                ).first()
                if not demographic:
                    continue
                responses = SurveyResponse.objects.filter(
                    user_id=user_id, company=company
                )

                row = [user_id, demographic.response_date.strftime("%Y-%m-%d %H:%M:%S")]

                # Add demographic data
                if company.code == "NHS":
                    row.extend([demographic.client_type])
                else:
                    # Add appropriate demographic fields for other companies
                    pass

                # Add responses
                response_dict = {resp.question_id: resp.response for resp in responses}
                for question in questions:
                    row.append(response_dict.get(question.id, ""))

                writer.writerow(row)
            except DemographicData.DoesNotExist:
                continue

    return response


@login_required
def demographic_analysis_view(request):
    """Detailed demographic analysis using existing data"""
    if not hasattr(request.user, "companyadmin"):
        return HttpResponse("You are not authorized to view this page", status=403)

    company_admin = request.user.companyadmin
    company = company_admin.company

    # Get all demographic data for this company
    demographics = DemographicData.objects.filter(company=company)
    total_respondents = demographics.count()

    # Get all survey responses for score calculations
    all_responses = SurveyResponse.objects.filter(company=company)
    total_responses = all_responses.count()

    # Calculate average score
    avg_score = all_responses.aggregate(avg=Avg("response"))["avg"] or 0

    # Calculate completion rate (simplified - you might want to adjust this)
    total_questions = SurveyQuestion.objects.filter(company=company).count()
    expected_responses = total_respondents * total_questions
    completion_rate = (
        (total_responses / expected_responses * 100) if expected_responses > 0 else 0
    )

    # Response rate (percentage of demographic entries that have survey responses)
    users_with_responses = all_responses.values("user_id").distinct().count()
    response_rate = (
        (users_with_responses / total_respondents * 100) if total_respondents > 0 else 0
    )

    # Demographic analysis data
    analysis_data = {}
    demographic_fields = []

    if company.code == "HIT":
        demographic_fields = [
            "gender",
            "age_group",
            "department",
            "contract_type",
            "designation",
            "highest_qualification",
            "category",
        ]
    else:
        demographic_fields = ["client_type"]

    # Optimize by prefetching related data
    for field in demographic_fields:
        field_analysis = []

        # Get unique values for this field
        unique_values = demographics.values_list(field, flat=True).distinct()

        for value in unique_values:
            if value:  # Only process non-empty values
                # Count demographics with this value
                demo_filter = {field: value}
                demos_with_value = demographics.filter(**demo_filter)
                count = demos_with_value.count()

                # Get user_ids for these demographics
                user_ids = demos_with_value.values_list("user_id", flat=True)

                # Calculate average score for these users
                user_responses = all_responses.filter(user_id__in=user_ids)
                response_count = user_responses.count()
                avg_score_value = (
                    user_responses.aggregate(avg=Avg("response"))["avg"] or 0
                )

                field_analysis.append(
                    {
                        "value": value,
                        "count": count,
                        "avg_score": avg_score_value,
                        "response_count": response_count,
                    }
                )

        # Sort by count descending
        field_analysis.sort(key=lambda x: x["count"], reverse=True)
        analysis_data[field] = field_analysis

    context = {
        "company": company,
        "analysis_data": analysis_data,
        "demographic_fields": demographic_fields,
        "total_respondents": total_respondents,
        "avg_score": avg_score,
        "completion_rate": round(completion_rate, 1),
        "response_rate": round(response_rate, 1),
    }

    return render(request, "demographic_analysis.html", context)


@login_required
def category_analysis_view(request, category):
    """Detailed analysis for a specific category"""
    if not hasattr(request.user, "companyadmin"):
        return HttpResponse("You are not authorized to view this page", status=403)

    company_admin = request.user.companyadmin
    company = company_admin.company

    # Get questions in this category
    questions = SurveyQuestion.objects.filter(company=company, category=category)

    # Get response statistics for each question
    question_stats = []
    for question in questions:
        stats = SurveyResponse.objects.filter(question=question).aggregate(
            avg_response=Avg("response"),
            total_responses=Count("id"),
            strongly_agree=Count("id", filter=Q(response=5)),
            agree=Count("id", filter=Q(response=4)),
            neutral=Count("id", filter=Q(response=3)),
            disagree=Count("id", filter=Q(response=2)),
            strongly_disagree=Count("id", filter=Q(response=1)),
        )
        question_stats.append({"question": question, "stats": stats})

    # Get category performance over time
    trend_data = (
        SurveyResponse.objects.filter(question__category=category, company=company)
        .extra({"date": "date(response_date)"})
        .values("date")
        .annotate(avg_score=Avg("response"))
        .order_by("date")
    )

    context = {
        "company": company,
        "category": category,
        "questions": questions,
        "question_stats": question_stats,
        "trend_data": list(trend_data),
    }

    return render(request, "category_analysis.html", context)


@login_required
def real_time_analytics_view(request):
    """Real-time analytics dashboard"""
    from django.db.models.functions import TruncHour, TruncDate
    from django.utils.timezone import now
    import datetime

    if not hasattr(request.user, "companyadmin"):
        return HttpResponse("You are not authorized to view this page", status=403)

    company_admin = request.user.companyadmin
    company = company_admin.company

    # Real-time data
    current_hour = now().replace(minute=0, second=0, microsecond=0)
    responses_last_hour = SurveyResponse.objects.filter(
        company=company, response_date__gte=current_hour
    ).count()

    responses_today = SurveyResponse.objects.filter(
        company=company, response_date__date=now().date()
    ).count()

    # Active users (responses in last 30 minutes)
    active_users = (
        SurveyResponse.objects.filter(
            company=company, response_date__gte=now() - timedelta(minutes=30)
        )
        .values("user_id")
        .distinct()
        .count()
    )

    # Response rate by hour (last 24 hours) - Fixed query
    hourly_data = (
        SurveyResponse.objects.filter(
            company=company, response_date__gte=now() - timedelta(hours=24)
        )
        .annotate(hour=TruncHour("response_date"))
        .values("hour")
        .annotate(count=Count("id"))
        .order_by("hour")
    )

    # Format hourly data for the template
    formatted_hourly_data = []
    for data in hourly_data:
        formatted_hourly_data.append(
            {"hour": data["hour"].strftime("%H:00"), "count": data["count"]}
        )

    context = {
        "company": company,
        "responses_last_hour": responses_last_hour,
        "responses_today": responses_today,
        "active_users": active_users,
        "hourly_data": formatted_hourly_data,
    }

    return render(request, "real_time_analytics.html", context)
