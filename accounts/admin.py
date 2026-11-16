from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "pen_name", "is_author", "coins", "checkin_streak")
    list_filter = ("is_author",)
    search_fields = ("user__email", "user__username", "pen_name")
