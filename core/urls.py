from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("assignments/add/", views.assignment_add, name="assignment_add"),
    path("applications/add/", views.application_add, name="application_add"),
    path("applications/<int:pk>/", views.application_detail, name="application_detail"),
    path("applications/<int:pk>/questionnaire/", views.questionnaire, name="questionnaire"),
    path("applications/<int:pk>/documents/add/", views.document_add, name="document_add"),
    path("applications/<int:pk>/export/", views.export_zip, name="export_zip"),
    path("documents/<int:pk>/download/", views.document_download, name="document_download"),
]
