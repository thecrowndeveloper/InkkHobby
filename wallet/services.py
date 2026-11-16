from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile

from .models import AuthorEarning, ChapterUnlock, CoinTransaction


class InsufficientCoins(Exception):
    def __init__(self, missing):
        super().__init__(f"{missing} more coins needed")
        self.missing = missing


def _locked_profile(user):
    profile, _ = Profile.objects.select_for_update().get_or_create(user=user)
    return profile


def _record(profile, amount, kind, note=""):
    return CoinTransaction.objects.create(
        user=profile.user, amount=amount, balance_after=profile.coins, kind=kind, note=note
    )


def credit(user, amount, kind, note=""):
    with transaction.atomic():
        profile = _locked_profile(user)
        profile.coins += amount
        profile.save(update_fields=["coins"])
        _record(profile, amount, kind, note)
        return profile.coins


def _next_streak(profile, today):
    if profile.last_checkin == today:
        return profile.checkin_streak
    if profile.last_checkin == today - timedelta(days=1):
        return profile.checkin_streak + 1
    return 1


def _reward_for(streak):
    return settings.DAILY_COIN_BASE + min(max(streak - 1, 0), settings.DAILY_COIN_MAX_BONUS)


def daily_status(profile):
    """What the Daily Ink widget needs: claimed today?, current streak, tomorrow's/today's reward."""
    today = timezone.localdate()
    claimed = profile.last_checkin == today
    if claimed:
        streak, reward = profile.checkin_streak, _reward_for(profile.checkin_streak + 1)
    else:
        alive = profile.last_checkin == today - timedelta(days=1)
        streak = profile.checkin_streak if alive else 0
        reward = _reward_for(_next_streak(profile, today))
    # A week-long strip: filled days so far, and which day is up next (if today isn't claimed yet).
    filled = (streak % 7 or 7) if (claimed and streak) else streak % 7
    days = [
        {"n": n, "filled": n <= filled, "next": (not claimed) and n == filled + 1}
        for n in range(1, 8)
    ]
    return {"claimed": claimed, "streak": streak, "reward": reward, "days": days}


def claim_daily(user):
    """Returns (coins, streak), or None if today's Daily Ink was already claimed."""
    with transaction.atomic():
        profile = _locked_profile(user)
        today = timezone.localdate()
        if profile.last_checkin == today:
            return None
        streak = _next_streak(profile, today)
        reward = _reward_for(streak)
        profile.coins += reward
        profile.last_checkin = today
        profile.checkin_streak = streak
        profile.save(update_fields=["coins", "last_checkin", "checkin_streak"])
        _record(profile, reward, CoinTransaction.Kind.DAILY, f"Day {streak} streak")
        return reward, streak


def unlock_chapter(user, chapter):
    """Spend coins to unlock a chapter. Returns True if newly unlocked, False if already unlocked."""
    book = chapter.book
    with transaction.atomic():
        profile = _locked_profile(user)  # lock first so double-clicks can't spend twice
        if ChapterUnlock.objects.filter(user=user, chapter=chapter).exists():
            return False
        price = chapter.price
        if profile.coins < price:
            raise InsufficientCoins(price - profile.coins)
        profile.coins -= price
        profile.save(update_fields=["coins"])
        ChapterUnlock.objects.create(user=user, chapter=chapter, coins_spent=price)
        _record(profile, -price, CoinTransaction.Kind.UNLOCK, f"{book.title} · Chapter {chapter.number}")

        # Authors earn only on books under an active contract.
        contract = book.contracts.filter(status="active").order_by("-created_at").first()
        if contract and price:
            AuthorEarning.objects.create(
                author=book.author,
                book=book,
                chapter=chapter,
                coins_spent=price,
                share_percent=contract.revenue_share_percent,
                author_coins=price * contract.revenue_share_percent // 100,
            )
        return True
