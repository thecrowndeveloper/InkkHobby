from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from books.models import Chapter
from pages.utils import safe_next

from . import services
from .models import CoinTransaction


@login_required
def wallet_home(request):
    profile = request.user.profile
    return render(
        request,
        "wallet/wallet.html",
        {
            "transactions": request.user.coin_transactions.all()[:30],
            "packs": settings.COIN_PACKS,
            "mock_payments": settings.PAYMENTS_MODE == "mock",
        },
    )


@login_required
@require_POST
def daily_claim(request):
    result = services.claim_daily(request.user)
    if result is None:
        messages.info(request, "You've already collected today's Daily Ink. Come back tomorrow.")
    else:
        coins, streak = result
        messages.success(request, f"+{coins} coins in your well. Day {streak} of your streak.")
    return redirect(safe_next(request, reverse("wallet:home")))


@login_required
@require_POST
def unlock(request, chapter_id):
    chapter = get_object_or_404(Chapter.objects.select_related("book"), pk=chapter_id, is_published=True, book__is_published=True)
    if chapter.is_free:
        return redirect(chapter.get_absolute_url())
    try:
        newly = services.unlock_chapter(request.user, chapter)
    except services.InsufficientCoins as exc:
        messages.error(request, f"You need {exc.missing} more coins to unlock this chapter. Claim your Daily Ink or top up your well.")
        return redirect(chapter.get_absolute_url())
    if newly:
        messages.success(request, f"Chapter {chapter.number} unlocked. Enjoy.")
    return redirect(chapter.get_absolute_url())


@login_required
@require_POST
def buy_pack(request, code):
    if settings.PAYMENTS_MODE != "mock":
        raise Http404  # real gateway integration goes here
    pack = next((p for p in settings.COIN_PACKS if p["code"] == code), None)
    if pack is None:
        raise Http404
    services.credit(request.user, pack["coins"], CoinTransaction.Kind.PURCHASE, "Test-mode top-up (no charge)")
    messages.success(request, f"{pack['coins']} test coins added.")
    return redirect("wallet:home")
