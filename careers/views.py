from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AuthorApplicationForm, JobApplicationForm
from .models import AuthorApplication, Job, JobApplication


@login_required  # per the brief: author benefits are visible to signed-in users only
def benefits(request):
    profile = request.user.profile
    application = request.user.author_applications.first()
    form = None
    if not profile.is_author and not (application and application.status == "pending"):
        form = AuthorApplicationForm(initial={"pen_name": profile.pen_name})
    return render(
        request,
        "careers/benefits.html",
        {"contracts": settings.CONTRACT_OPTIONS, "application": application, "form": form},
    )


@login_required
@require_POST
def author_apply(request):
    if request.user.profile.is_author:
        return redirect("careers:benefits")
    if request.user.author_applications.filter(status="pending").exists():
        messages.info(request, "Your application is already with our editors.")
        return redirect("careers:benefits")
    form = AuthorApplicationForm(request.POST)
    if form.is_valid():
        application = form.save(commit=False)
        application.user = request.user
        application.save()
        messages.success(request, "Application received. We read every one, and we'll be in touch.")
        return redirect("careers:benefits")
    return render(
        request,
        "careers/benefits.html",
        {"contracts": settings.CONTRACT_OPTIONS, "application": None, "form": form},
        status=400,
    )


def job_list(request):
    jobs = Job.objects.filter(status="open")
    category = request.GET.get("category", "")
    if category in dict(Job.Category.choices):
        jobs = jobs.filter(category=category)
    page = Paginator(jobs, 12).get_page(request.GET.get("page"))
    return render(
        request,
        "careers/jobs.html",
        {"page": page, "categories": Job.Category.choices, "category": category},
    )


def job_detail(request, slug):
    job = get_object_or_404(Job, slug=slug)
    applied = request.user.is_authenticated and job.applications.filter(applicant=request.user).exists()
    return render(
        request,
        "careers/job_detail.html",
        {"job": job, "applied": applied, "form": JobApplicationForm()},
    )


@login_required
@require_POST
def job_apply(request, slug):
    job = get_object_or_404(Job, slug=slug, status="open")
    if job.applications.filter(applicant=request.user).exists():
        messages.info(request, "You've already applied for this one.")
        return redirect(job.get_absolute_url())
    form = JobApplicationForm(request.POST)
    if form.is_valid():
        application = form.save(commit=False)
        application.job = job
        application.applicant = request.user
        application.save()
        messages.success(request, "Application sent.")
        return redirect(job.get_absolute_url())
    return render(request, "careers/job_detail.html", {"job": job, "applied": False, "form": form}, status=400)
