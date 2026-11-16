import json
import urllib.error
import urllib.request

from django.conf import settings

from .models import TranslationCache
from .text import split_paragraphs

ENDPOINT = "https://translation.googleapis.com/language/translate/v2"
BATCH = 40


class TranslationUnavailable(Exception):
    pass


def supported(lang):
    return lang in {code for code, _ in settings.TRANSLATION_LANGUAGES}


def translate_chapter(chapter, lang):
    """Return the chapter's paragraphs in `lang`, using the cache when the source text hasn't changed."""
    cached = TranslationCache.objects.filter(chapter=chapter, language=lang).first()
    if cached and cached.source_checksum == chapter.checksum:
        return cached.paragraphs

    key = settings.GOOGLE_TRANSLATE_API_KEY
    if not key:
        raise TranslationUnavailable("Translation isn't switched on yet.")

    paragraphs = split_paragraphs(chapter.body)
    out = []
    for i in range(0, len(paragraphs), BATCH):
        payload = {"q": paragraphs[i : i + BATCH], "target": lang, "format": "text", "source": chapter.book.language}
        req = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-goog-api-key": key},
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.load(resp)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise TranslationUnavailable("The translator is resting. Please try again in a moment.") from exc
        out.extend(t["translatedText"] for t in data["data"]["translations"])

    TranslationCache.objects.update_or_create(
        chapter=chapter,
        language=lang,
        defaults={"source_checksum": chapter.checksum, "paragraphs": out},
    )
    return out
