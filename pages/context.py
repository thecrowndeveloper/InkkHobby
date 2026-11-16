from django.conf import settings
from django.core.cache import cache

from wallet.services import daily_status


def _nav_genres():
    from books.models import Genre

    return list(Genre.objects.values("name", "slug")[:14])


def site(request):
    ctx = {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_CONTACT_EMAIL": settings.SITE_CONTACT_EMAIL,
        "nav_genres": cache.get_or_set("nav_genres", _nav_genres, 300),
    }
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        from accounts.models import Profile

        profile, _ = Profile.objects.get_or_create(user=user)
        ctx["my_profile"] = profile
        ctx["daily"] = daily_status(profile)
    return ctx
