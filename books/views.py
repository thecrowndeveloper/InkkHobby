from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from careers.models import Contract
from pages.utils import safe_next
from wallet.models import ChapterUnlock

from . import translation
from .access import can_read, is_owner
from .forms import CommentForm, ReviewForm
from .models import Book, Chapter, Follow, Genre, LibraryEntry, ReadingProgress, Review

User = get_user_model()

SORTS = {
    "trending": "Trending",
    "new": "Newest",
    "updated": "Recently updated",
    "rating": "Top rated",
    "longest": "Longest",
}


def _cards():
    return Book.objects.published().prefetch_related("genres")


def _continue_reading(user, limit=6):
    """Books the reader has started, newest first, with the chapter they're on and how far through they are."""
    rows = list(
        ReadingProgress.objects.filter(user=user, book__is_published=True)
        .select_related("book__author__profile", "chapter")[:limit]
    )
    totals = dict(
        Chapter.objects.filter(book__in=[r.book_id for r in rows], is_published=True)
        .values_list("book_id")
        .annotate(n=Count("id"))
    )
    for r in rows:
        total = totals.get(r.book_id, 0) or 1
        r.total = total
        r.percent = min(100, round(r.chapter.number / total * 100))
    return rows


def home(request):
    trending = list(_cards().trending()[:10])
    fresh = _cards().with_stats().order_by("-updated_at")[:10]
    exclusive_ids = Contract.objects.filter(status="active", contract_type="exclusive").values("book_id")
    exclusives = _cards().with_stats().filter(pk__in=exclusive_ids)[:12]
    return render(
        request,
        "home.html",
        {
            "spotlight": trending[:5],
            "top_ten": trending,
            "fresh": fresh,
            "exclusives": exclusives,
            "genres": Genre.objects.all(),
            "continue_reading": _continue_reading(request.user) if request.user.is_authenticated else [],
        },
    )


def browse(request, genre_slug=None):
    genre = get_object_or_404(Genre, slug=genre_slug) if genre_slug else None
    q = request.GET.get("q", "").strip()
    kind = request.GET.get("kind", "")
    status = request.GET.get("status", "")
    sort = request.GET.get("sort", "trending")
    if sort not in SORTS:
        sort = "trending"

    qs = _cards()
    if genre:
        qs = qs.filter(genres=genre)
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(synopsis__icontains=q)
            | Q(author__profile__pen_name__icontains=q)
            | Q(genres__name__icontains=q)
        ).distinct()
    if kind in dict(Book.Kind.choices):
        qs = qs.filter(kind=kind)
    if status in dict(Book.Status.choices):
        qs = qs.filter(status=status)

    if sort == "trending":
        qs = qs.trending()
    else:
        qs = qs.with_stats()
        qs = {
            "new": qs.order_by("-created_at"),
            "updated": qs.order_by("-updated_at"),
            "rating": qs.order_by(F("avg_rating").desc(nulls_last=True), "-review_count"),
            "longest": qs.order_by("-word_count"),
        }[sort]

    page = Paginator(qs, 18).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "books/browse.html",
        {
            "page": page,
            "genre": genre,
            "genres": Genre.objects.all(),
            "q": q,
            "kind": kind,
            "status": status,
            "sort": sort,
            "sorts": SORTS,
            "kinds": Book.Kind.choices,
            "statuses": Book.Status.choices,
            "querystring": params.urlencode(),
        },
    )


def book_detail(request, slug):
    book = get_object_or_404(Book.objects.with_stats().prefetch_related("genres"), slug=slug)
    owner = is_owner(request.user, book)
    if not book.is_published and not owner:
        raise Http404
    if not owner:
        Book.objects.filter(pk=book.pk).update(views=F("views") + 1)

    chapters = list(book.chapters.filter(is_published=True))
    for ch in chapters:
        ch.book = book  # avoid one query per chapter for price/is_free
    ctx = {
        "book": book,
        "chapters": chapters,
        "first_chapter": chapters[0] if chapters else None,
        "reviews": book.reviews.select_related("user__profile")[:20],
        "review_form": ReviewForm(),
        "contract": book.contracts.filter(status="active").order_by("-created_at").first(),
        "unlocked_ids": set(),
        "in_library": False,
        "following": False,
        "my_review": None,
        "resume": None,
        "share_url": request.build_absolute_uri(book.get_absolute_url()),
    }
    if request.user.is_authenticated:
        progress = ReadingProgress.objects.filter(user=request.user, book=book).select_related("chapter").first()
        ctx["resume"] = progress.chapter if progress else None
        ctx["unlocked_ids"] = set(
            ChapterUnlock.objects.filter(user=request.user, chapter__book=book).values_list("chapter_id", flat=True)
        )
        ctx["in_library"] = LibraryEntry.objects.filter(user=request.user, book=book).exists()
        ctx["following"] = Follow.objects.filter(follower=request.user, author=book.author).exists()
        ctx["my_review"] = Review.objects.filter(user=request.user, book=book).first()
        if ctx["my_review"]:
            ctx["review_form"] = ReviewForm(instance=ctx["my_review"])
    return render(request, "books/detail.html", ctx)


def _chapter_or_404(request, slug, number):
    book = get_object_or_404(Book.objects.select_related("author__profile"), slug=slug)
    chapter = get_object_or_404(Chapter, book=book, number=number)
    chapter.book = book
    if (not book.is_published or not chapter.is_published) and not is_owner(request.user, book):
        raise Http404
    return book, chapter


def chapter_detail(request, slug, number):
    book, chapter = _chapter_or_404(request, slug, number)
    readable = can_read(request.user, chapter)
    if readable and request.user.is_authenticated:
        ReadingProgress.objects.update_or_create(user=request.user, book=book, defaults={"chapter": chapter})

    published = book.chapters.filter(is_published=True)
    ctx = {
        "book": book,
        "chapter": chapter,
        "readable": readable,
        "prev_chapter": published.filter(number__lt=number).order_by("-number").first(),
        "next_chapter": published.filter(number__gt=number).order_by("number").first(),
        "share_url": request.build_absolute_uri(chapter.get_absolute_url()),
        "share_title": f"{book.title}, Chapter {chapter.number}",
        "languages": settings.TRANSLATION_LANGUAGES,
        "comment_form": CommentForm(),
        "comments": chapter.comments.select_related("user__profile")[:40] if readable else [],
        "preview": [] if readable else chapter.preview_paragraphs(),
        "in_library": request.user.is_authenticated
        and LibraryEntry.objects.filter(user=request.user, book=book).exists(),
    }
    return render(request, "books/chapter.html", ctx)


@login_required
@require_GET
def chapter_translate(request, slug, number):
    book, chapter = _chapter_or_404(request, slug, number)
    if not can_read(request.user, chapter):
        return JsonResponse({"error": "Unlock this chapter to translate it."}, status=403)
    lang = request.GET.get("lang", "")
    if not translation.supported(lang):
        return JsonResponse({"error": "That language isn't available yet."}, status=400)
    try:
        paragraphs = translation.translate_chapter(chapter, lang)
    except translation.TranslationUnavailable as exc:
        return JsonResponse({"error": str(exc)}, status=503)
    return JsonResponse({"paragraphs": paragraphs, "language": lang})


@login_required
@require_POST
def comment_submit(request, slug, number):
    book, chapter = _chapter_or_404(request, slug, number)
    if can_read(request.user, chapter):
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.chapter, comment.user = chapter, request.user
            comment.save()
            messages.success(request, "Comment posted.")
        else:
            messages.error(request, "Write something first, then post.")
    return redirect(f"{chapter.get_absolute_url()}#comments")


@login_required
@require_POST
def review_submit(request, slug):
    book = get_object_or_404(Book, slug=slug, is_published=True)
    existing = Review.objects.filter(user=request.user, book=book).first()
    form = ReviewForm(request.POST, instance=existing)
    if form.is_valid():
        review = form.save(commit=False)
        review.book, review.user = book, request.user
        review.save()
        messages.success(request, "Thank you for your review.")
    else:
        messages.error(request, "Please choose a rating from 1 to 5.")
    return redirect(f"{book.get_absolute_url()}#reviews")


@login_required
@require_POST
def library_toggle(request, slug):
    book = get_object_or_404(Book, slug=slug, is_published=True)
    entry, created = LibraryEntry.objects.get_or_create(user=request.user, book=book)
    if created:
        messages.success(request, f"“{book.title}” is on your shelf.")
    else:
        entry.delete()
        messages.info(request, f"“{book.title}” removed from your library.")
    return redirect(safe_next(request, book.get_absolute_url()))


@login_required
def my_library(request):
    ids = request.user.library.values("book_id")
    books = _cards().with_stats().filter(pk__in=ids).order_by("-updated_at")
    return render(request, "books/library.html", {"books": books})


def writer(request, pk):
    author = get_object_or_404(User.objects.select_related("profile"), pk=pk)
    books = _cards().with_stats().filter(author=author).order_by("-updated_at")
    return render(
        request,
        "books/writer.html",
        {
            "writer": author,
            "books": books,
            "follower_count": author.followers.count(),
            "following": request.user.is_authenticated
            and Follow.objects.filter(follower=request.user, author=author).exists(),
        },
    )


@login_required
@require_POST
def follow_toggle(request, pk):
    author = get_object_or_404(User, pk=pk)
    if author == request.user:
        messages.info(request, "You can't follow yourself, though we admire the confidence.")
    else:
        follow, created = Follow.objects.get_or_create(follower=request.user, author=author)
        if not created:
            follow.delete()
    return redirect(safe_next(request, f"/writers/{pk}/"))
