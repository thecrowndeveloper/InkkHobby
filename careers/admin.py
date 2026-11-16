from django.contrib import admin, messages
from django.utils import timezone

from .models import AuthorApplication, Contract, Job, JobApplication


@admin.register(AuthorApplication)
class AuthorApplicationAdmin(admin.ModelAdmin):
    list_display = ("pen_name", "user", "status", "created_at")
    list_filter = ("status",)
    actions = ["approve", "decline"]

    @admin.action(description="Approve selected applications (makes the user an author)")
    def approve(self, request, queryset):
        count = 0
        for app in queryset.exclude(status="approved").select_related("user__profile"):
            profile = app.user.profile
            profile.is_author = True
            profile.pen_name = app.pen_name
            profile.bio = profile.bio or app.bio
            profile.save()
            app.status = "approved"
            app.reviewed_at = timezone.now()
            app.save()
            count += 1
        self.message_user(request, f"{count} author(s) approved.", messages.SUCCESS)

    @admin.action(description="Decline selected applications")
    def decline(self, request, queryset):
        queryset.filter(status="pending").update(status="declined", reviewed_at=timezone.now())


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("book", "contract_type", "revenue_share_percent", "status", "start_date")
    list_filter = ("contract_type", "status")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "pay", "status", "created_at")
    list_filter = ("category", "status")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "created_at")
