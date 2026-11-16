from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class AuthorApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        DECLINED = "declined", "Declined"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="author_applications", on_delete=models.CASCADE)
    pen_name = models.CharField(max_length=60)
    bio = models.TextField(max_length=1200)
    sample = models.TextField(max_length=6000, help_text="A short sample of your writing")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.pen_name} ({self.get_status_display()})"


class Contract(models.Model):
    class Type(models.TextChoices):
        EXCLUSIVE = "exclusive", "Exclusive"
        NON_EXCLUSIVE = "non_exclusive", "Non-exclusive"

    class Status(models.TextChoices):
        OFFERED = "offered", "Offered"
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"

    book = models.ForeignKey("books.Book", related_name="contracts", on_delete=models.CASCADE)
    contract_type = models.CharField(max_length=14, choices=Type.choices)
    revenue_share_percent = models.PositiveSmallIntegerField(help_text="Author's share of coins spent on this book")
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.OFFERED)
    terms = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.book} · {self.get_contract_type_display()} ({self.get_status_display()})"


class Job(models.Model):
    class Category(models.TextChoices):
        EDITOR = "editor", "Editor"
        PROOFREADER = "proofreader", "Proofreader"
        TRANSLATOR = "translator", "Translator"
        WRITER = "writer", "Writer / ghostwriter"
        OTHER = "other", "Other writing work"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    category = models.CharField(max_length=12, choices=Category.choices)
    description = models.TextField()
    pay = models.CharField(max_length=80, blank=True, help_text='e.g. "₦25,000 per project"')
    language = models.CharField(max_length=40, default="English")
    remote = models.BooleanField(default=True)
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:130] or "job"
            slug, n = base, 2
            while Job.objects.filter(slug=slug).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("careers:job", args=[self.slug])


class JobApplication(models.Model):
    job = models.ForeignKey(Job, related_name="applications", on_delete=models.CASCADE)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="job_applications", on_delete=models.CASCADE)
    note = models.TextField(max_length=2000)
    portfolio_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["job", "applicant"], name="one_application_per_job")]
