from django.urls import path, include
from a_home.views import *
from .reports import *

urlpatterns = [
    path("start/", demographic_data_view, name="start"),
    path(
        "feedback/<int:user_id>/details/",
        feedback_details,
        name="detailed_feedback_page",
    ),
    path(
        "download-all-responses/", download_all_responses, name="download_all_responses"
    ),
    path("thank-you/", thank_you, name="thank_you"),
    path("job-satisfaction/", job_satisfaction_view, name="job_satisfaction"),
    path("aggregated-feedback/", aggregated_feedback_view, name="aggregated_feedback"),
    path("staff/", staff_dashboard_view, name="staff_dashboard"),
    path("feedbacks/", feedback_list, name="feedback_list"),
    path("feedbacks/details/", feedback_detail, name="feedback_detail"),
    path("generate-full-report/", generate_full_report, name="generate_full_report"),
    path("report/department/", generate_department_report, name="department_report"),
    path("report/designation/", generate_designation_report, name="designation_report"),
    path(
        "report/qualification/",
        generate_qualification_report,
        name="qualification_report",
    ),
    path("report/age-group/", generate_age_group_report, name="age_group_report"),
    path("", home_view, name="home"),
]
