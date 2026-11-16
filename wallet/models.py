from django.conf import settings
from django.db import models


class CoinTransaction(models.Model):
    """Append-only ledger. Profile.coins is the running balance; this explains every change."""

    class Kind(models.TextChoices):
        DAILY = "daily", "Daily Ink"
        PURCHASE = "purchase", "Coin purchase"
        UNLOCK = "unlock", "Chapter unlock"
        BONUS = "bonus", "Bonus"
        ADJUSTMENT = "adjustment", "Adjustment"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="coin_transactions", on_delete=models.CASCADE)
    amount = models.IntegerField(help_text="Positive = credit, negative = spend")
    balance_after = models.PositiveIntegerField()
    kind = models.CharField(max_length=12, choices=Kind.choices)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class ChapterUnlock(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="unlocks", on_delete=models.CASCADE)
    chapter = models.ForeignKey("books.Chapter", related_name="unlocks", on_delete=models.CASCADE)
    coins_spent = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "chapter"], name="unique_unlock")]


class AuthorEarning(models.Model):
    """Recorded whenever a reader unlocks a chapter of a book under an active contract."""

    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="earnings", on_delete=models.CASCADE)
    book = models.ForeignKey("books.Book", related_name="earnings", on_delete=models.CASCADE)
    chapter = models.ForeignKey("books.Chapter", related_name="earnings", on_delete=models.CASCADE)
    coins_spent = models.PositiveIntegerField()
    share_percent = models.PositiveSmallIntegerField()
    author_coins = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
