# InkHobby

A premium reading and writing platform: web novels, fanfiction, manga and anime stories, with paid chapter unlocking, Daily Ink free coins, author contracts, a writer job board and chapter translation.

**Stack:** Django 5/6 (Python), server-rendered templates with a small amount of vanilla JavaScript, PostgreSQL, django-allauth (email + Google sign-in), WhiteNoise.
Chosen because stories need fast, crawlable, typographically precise pages, and Django gives auth, admin, i18n and safe database transactions (the coin ledger) out of the box.

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then export the variables, or set them in your shell
python manage.py makemigrations accounts books wallet careers pages
python manage.py migrate
python manage.py seed_demo      # optional demo stories, authors and jobs
python manage.py createsuperuser
python manage.py runserver
```

With no `DB_NAME` set it uses SQLite. For PostgreSQL set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`.
Run the tests with `python manage.py test`.

### Google sign-in
Create an OAuth client in Google Cloud Console, add redirect URI `http://localhost:8000/accounts/google/login/callback/`, then set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. In `/admin/` > Sites, set the domain to match your host.

### Translation
Set `GOOGLE_TRANSLATE_API_KEY` (Cloud Translation API). Translations are cached per chapter and language. Add languages in `TRANSLATION_LANGUAGES` in `config/settings.py`.

## Updating an existing local copy

If you already ran the first version, copy these files over it, then:

```bash
python manage.py makemigrations books
python manage.py migrate
```

(New model: `ReadingProgress`, which powers Continue reading.)

## Design system

- **Type:** Inter for the interface and headings, Lora for reading text and synopses. No italics, no decorative faces.
- **Colour:** dark by default (light theme via the header toggle). One accent (ember) for actions; amber is reserved for coins.
- **Covers:** uploaded images when present; otherwise every title gets its own generated cover (three artwork styles, colour derived from the title).
- **Reading room:** dark, light and sepia themes, text size and line width controls, a progress line, and ← / → keys for previous and next chapter.
- All styling lives in `static/css/inkhobby.css`; tokens are at the top.

## What's built (phase 1: reader core)

- Homepage: spotlight hero, Continue reading, Daily Ink week strip, ranked Top 10, genres, exclusives, new chapters
- Browse, search, genre pages, filters and sorting
- Book pages: cover (or generated cover), synopsis, word count, chapters with free/locked state, reviews, library, follow author, share
- Reading room: three themes, adjustable size and width, progress line, translation menu
- Chapter locking: first N chapters free per book, the rest cost coins; unlocks are atomic and idempotent
- Daily Ink: streak-based daily coins; full coin ledger
- Author benefits page (login required), author application, admin approval
- Contracts (exclusive / non-exclusive) and per-unlock author earnings on contracted books
- Job board with applications
- About, Contact, FAQs, Terms, Privacy; welcome guide for first-time visitors

## Placeholders you must replace before launch

- `COIN_PACKS` prices and `CONTRACT_OPTIONS` shares in `config/settings.py` are sample values.
- `PAYMENTS_MODE=mock` adds coins without charging. Wire Paystack/Flutterwave/Stripe in `wallet/views.py::buy_pack` and set the mode accordingly. In any other mode the mock endpoint returns 404.
- Terms and Privacy are starter drafts. Have a lawyer review them. FAQ answers (for example "coins don't expire") state policy, so confirm them.
- Uploaded media (covers, avatars) is served by Django only in DEBUG. Use S3/Cloudinary or a media volume in production.

## Phase 2 roadmap

1. Author dashboard: create books, write and schedule chapters, upload covers, see earnings
2. Real payments plus author payout workflow (coins to currency)
3. Editor/proofreader workflow on the job board (assignments, delivery, payment)
4. Manga/image chapters, comment moderation, notifications, email digests
5. Time-decayed trending, full-text search (PostgreSQL), SEO sitemap and structured data
