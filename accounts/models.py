from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE)
    pen_name = models.CharField(max_length=60, blank=True)
    bio = models.TextField(blank=True, max_length=1200)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    is_author = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=8, default="en")

    # Coin wallet (every change goes through wallet.services so the ledger stays honest).
    coins = models.PositiveIntegerField(default=0)
    last_checkin = models.DateField(null=True, blank=True)
    checkin_streak = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.pen_name or self.user.get_short_name() or self.user.get_username()
