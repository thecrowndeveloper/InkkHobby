from django import template
from django.utils.html import format_html, format_html_join

from books.text import split_paragraphs

register = template.Library()


@register.filter
def paragraphs(text):
    """Render plain text as escaped <p> elements."""
    return format_html_join("\n", "<p>{}</p>", ((p,) for p in split_paragraphs(text)))


@register.filter
def para_list(items):
    """Render an already-split list of paragraphs (e.g. a preview) as escaped <p> elements."""
    return format_html_join("\n", "<p>{}</p>", ((p,) for p in items))


@register.filter
def compact(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return value
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n / 1_000:.1f}k".replace(".0k", "k")
    return str(n)


@register.filter
def rounded(value):
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return 0


@register.filter
def reading_time(words):
    try:
        return max(1, round(int(words) / 230))
    except (TypeError, ValueError):
        return 1


@register.filter
def read_length(words):
    """'45 min' or '3 h 20 min', at ~230 words per minute."""
    try:
        minutes = max(1, round(int(words) / 230))
    except (TypeError, ValueError):
        return "—"
    hours, mins = divmod(minutes, 60)
    if not hours:
        return f"{mins} min"
    return f"{hours} h {mins} min" if mins else f"{hours} h"


@register.simple_tag
def stars(rating):
    full = rounded(rating)
    return format_html(
        '<span class="stars" aria-label="{} out of 5">{}{}</span>',
        full,
        "★" * full,
        format_html('<span class="stars__off">{}</span>', "★" * (5 - full)),
    )
