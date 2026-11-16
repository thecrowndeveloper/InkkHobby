from django.urls import path

from . import views

app_name = "careers"

urlpatterns = [
    path("authors/benefits/", views.benefits, name="benefits"),
    path("authors/apply/", views.author_apply, name="author_apply"),
    path("jobs/", views.job_list, name="jobs"),
    path("jobs/<slug:slug>/", views.job_detail, name="job"),
    path("jobs/<slug:slug>/apply/", views.job_apply, name="job_apply"),
]
