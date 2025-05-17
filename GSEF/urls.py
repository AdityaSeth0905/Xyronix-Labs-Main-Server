from django.urls import path
from .views import (
    ApplicantsView, ApplicantDetailView, ApplicantsRangeView,
    ApplicantEmailView, ApplicantAuthView, PingDatabaseView,
    ApplicantExistsView, ApplicantCreateView
)

urlpatterns = [
    path("applicants/", ApplicantsView.as_view()),
    path("applicant/<str:application_id>/", ApplicantDetailView.as_view()),
    path("applicants/range/", ApplicantsRangeView.as_view()),
    path("applicant/email/<str:email>/", ApplicantEmailView.as_view()),
    path("applicant/auth/<str:application_id>/", ApplicantAuthView.as_view()),
    path("ping/", PingDatabaseView.as_view()),
    path("applicant/exists/<str:application_id>/", ApplicantExistsView.as_view()),
    path('applicant/create/', ApplicantCreateView.as_view()),
]


