from django.urls import path
from .views import (
    ApplicantsView, ApplicantDetailView, ApplicantsRangeView, ApplicantEmailView, ApplicantAuthView, 
    PingDatabaseView, ApplicantExistsView, ApplicantCreateView, CustomLoginView, RegisterUserView, 
    UpdateApplicationStatusView, ApplicationsAfterIDView, AcceptedApplicationsView, 
    PendingApplicationsView, PendingApplicationsDataView, ApplicantDeleteView, APIDeepHealthCheckView, 
    APIDocumentationDownloadView, ApplicantTimestampsView, APISelfDocView, 
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
    path('auth/login/', CustomLoginView.as_view()),
    path('auth/register/', RegisterUserView.as_view()),
    path('auth/update-status/', UpdateApplicationStatusView.as_view()),  # For JSON body
    path('auth/update-status/<str:application_id>/<str:status_code>/', UpdateApplicationStatusView.as_view()),  # For URL params
    # Analytics endpoints, both API and manual (with optional params)
    path('applications/new/', ApplicationsAfterIDView.as_view()),
    path('applications/after/<int:after_id>/', ApplicationsAfterIDView.as_view()),  # Manual: /applications/after/27/
    path('applications/accepted/', AcceptedApplicationsView.as_view()),
    path('applications/accepted/<str:status_code>/', AcceptedApplicationsView.as_view()),  # Manual: /applications/accepted/A100/
    path('applications/pending/', PendingApplicationsView.as_view()),
    path('applications/pending/<str:status_code>/', PendingApplicationsView.as_view()),  # Manual: /applications/pending/pending/
    path('applications/pending-data/', PendingApplicationsDataView.as_view()),
    path('applications/pending-data/<str:status_code>/', PendingApplicationsDataView.as_view()),  # Manual: /applications/pending-data/pending/
    path('applicant/delete/', ApplicantDeleteView.as_view()),  # API: POST with JSON body
    path('applicant/delete/<str:application_id>/', ApplicantDeleteView.as_view()),  # Manual: POST with URL param
    path('health/report/', APIDeepHealthCheckView.as_view()),
    path('docs/manual/', APIDocumentationDownloadView.as_view()),
    path('applicant/timestamps/<str:application_id>/', ApplicantTimestampsView.as_view()),
    path('docs/apis/', APISelfDocView.as_view()),
]


