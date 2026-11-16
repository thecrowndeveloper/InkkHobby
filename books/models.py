import hashlib

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count, F, Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .text import preview


class Genre(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)
    blurb = models.CharField(max_length=160, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("books:genre", args=[self.slug])


class BookQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def with_stats(self):
        return self.select_related("author__profile").annotate(
            avg_rating=Avg("reviews__rating"),
            review_count=Count("reviews", distinct=True),
            library_count=Count("library_entries", distinct=True),
            chapter_count=Count("chapters", filter=Q(chapters__is_published=True), distinct=True),
        )

    def trending(self):
        # Simple, explainable heat score. Swap for a time-decayed score once there is traffic.
        return (
            self.with_stats()
            .annotate(score=F("views") + 5 * F("library_count") + 8 * F("review_count"))
            .order_by("-score", "-updated_at")
        )


class Book(models.Model):
    class Kind(models.TextChoices):
        WEBNOVEL = "webnovel", "Web novel"
        NOVEL = "novel", "Novel"
        FANFIC = "fanfic", "Fanfiction"
        MANGA = "manga", "Manga"
        ANIME = "anime", "Anime story"

    class Status(models.TextChoices):
        ONGOING = "ongoing", "Ongoing"
        COMPLETED = "completed", "Completed"
        HIATUS = "hiatus", "On hiatus"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="books", on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    synopsis = models.TextField(max_length=3000)
    cover = models.ImageField(upload_to="covers/", blank=True)
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.WEBNOVEL)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ONGOING)
    genres = models.ManyToManyField(Genre, related_name="books", blank=True)
    language = models.CharField(max_length=8, default="en")
    mature = models.BooleanField(default=False, help_text="Contains mature themes")

    free_chapters = models.PositiveSmallIntegerField(default=3, help_text="The first N chapters are free to read")
    default_chapter_price = models.PositiveSmallIntegerField(default=5, help_text="Coins per locked chapter")

    views = models.PositiveIntegerField(default=0)
    word_count = models.PositiveIntegerField(default=0, editable=False)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BookQuerySet.as_manager()

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:150] or "story"
            slug, n = base, 2
            while Book.objects.filter(slug=slug).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("books:detail", args=[self.slug])

    @property
    def cover_hue(self):
        # Every book without a cover gets its own colour so shelves never look identical.
        return sum(ord(c) * (i + 1) for i, c in enumerate(self.title)) % 360

    @property
    def cover_variant(self):
        # Three artwork styles for generated covers, picked from the title.
        return sum(ord(c) for c in self.title) % 3

    def recount_words(self):
        total = self.chapters.filter(is_published=True).aggregate(t=Sum("word_count"))["t"] or 0
        self.word_count = total
        self.updated_at = timezone.now()
        self.save(update_fields=["word_count", "updated_at"])


class Chapter(models.Model):
    book = models.ForeignKey(Book, related_name="chapters", on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=160)
    body = models.TextField(help_text="Plain text. Separate paragraphs with a blank line.")
    word_count = models.PositiveIntegerField(default=0, editable=False)
    coin_price = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Leave empty to use the book's default price"
    )
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["number"]
        constraints = [models.UniqueConstraint(fields=["book", "number"], name="unique_chapter_number")]

    def __str__(self):
        return f"{self.book.title} · Chapter {self.number}"

    def save(self, *args, **kwargs):
        self.word_count = len(self.body.split())
        super().save(*args, **kwargs)
        self.book.recount_words()

    def delete(self, *args, **kwargs):
        book = self.book
        super().delete(*args, **kwargs)
        book.recount_words()

    def get_absolute_url(self):
        return reverse("books:chapter", args=[self.book.slug, self.number])

    @property
    def price(self):
        return self.coin_price if self.coin_price is not None else self.book.default_chapter_price

    @property
    def is_free(self):
        return self.number <= self.book.free_chapters or self.price == 0

    @property
    def checksum(self):
        return hashlib.sha256(self.body.encode("utf-8")).hexdigest()

    def preview_paragraphs(self, words=80):
        return preview(self.body, words)


class TranslationCache(models.Model):
    chapter = models.ForeignKey(Chapter, related_name="translations", on_delete=models.CASCADE)
    language = models.CharField(max_length=8)
    source_checksum = models.CharField(max_length=64)
    paragraphs = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["chapter", "language"], name="unique_chapter_translation")]


class Review(models.Model):
    book = models.ForeignKey(Book, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="reviews", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(max_length=2000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [models.UniqueConstraint(fields=["book", "user"], name="one_review_per_user")]


class Comment(models.Model):
    chapter = models.ForeignKey(Chapter, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="comments", on_delete=models.CASCADE)
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class LibraryEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="library", on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name="library_entries", on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added_at"]
        constraints = [models.UniqueConstraint(fields=["user", "book"], name="unique_library_entry")]


class ReadingProgress(models.Model):
    """The chapter a reader last opened in each book, so we can say 'continue where you left off'."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="reading_progress", on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name="reading_progress", on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, related_name="+", on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [models.UniqueConstraint(fields=["user", "book"], name="one_progress_per_book")]


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="following", on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="followers", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "author"], name="unique_follow"),
            models.CheckConstraint(condition=~models.Q(follower=models.F("author")), name="no_self_follow"),
        ]
