from django.urls import path, include
from a_home.views import *
from .reports import *

urlpatterns = [
    path("", home_view, name="home"),
    path("demographic/", demographic_data_view, name="demographic_data"),
    path("survey/", survey_questions_view, name="survey_questions"),
    path("thank-you/", thank_you, name="thank_you"),
    path("review-submitted/", review_submitted, name="review_submitted"),
    # Company admin routes
    path("company/dashboard/", company_dashboard_view, name="company_dashboard"),
    path("reports/", company_reports_view, name="company_reports"),
    path("response/<str:user_id>/", response_detail_view, name="response_detail"),
    path("export/csv/", export_responses_csv, name="export_responses_csv"),
    path(
        "demographic-analysis/", demographic_analysis_view, name="demographic_analysis"
    ),
    path("category/<str:category>/", category_analysis_view, name="category_analysis"),
    path("real-time/", real_time_analytics_view, name="real_time_analytics"),
]
