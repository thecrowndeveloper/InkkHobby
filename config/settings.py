import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=""):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    return env(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# --- Core -------------------------------------------------------------------
DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-change-me")
if not DEBUG and SECRET_KEY == "dev-only-change-me":
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY when DJANGO_DEBUG is false.")

ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in env("DJANGO_CSRF_TRUSTED_ORIGINS").split(",") if o.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "accounts",
    "books",
    "wallet",
    "careers",
    "pages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "pages.context.site",
            ],
        },
    },
]

# --- Database: PostgreSQL when DB_NAME is set, SQLite otherwise ---------------
if env("DB_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST", "localhost"),
            "PORT": env("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- i18n / time --------------------------------------------------------------
LANGUAGE_CODE = "en"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

# --- Static / media -----------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# --- Auth (email + Google) ----------------------------------------------------
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", "optional")
SOCIALACCOUNT_AUTO_SIGNUP = True

if env("GOOGLE_CLIENT_ID"):
    SOCIALACCOUNT_PROVIDERS = {
        "google": {
            "SCOPE": ["profile", "email"],
            "AUTH_PARAMS": {"access_type": "online"},
            "APP": {"client_id": env("GOOGLE_CLIENT_ID"), "secret": env("GOOGLE_CLIENT_SECRET"), "key": ""},
        }
    }

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_PORT = int(env("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = True
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DEFAULT_FROM_EMAIL = env("SITE_CONTACT_EMAIL", "hello@inkhobby.com")

# --- InkHobby product settings --------------------------------------------------
SITE_NAME = "InkHobby"
SITE_CONTACT_EMAIL = env("SITE_CONTACT_EMAIL", "hello@inkhobby.com")

# Daily Ink: base coins per day, plus +1 per consecutive day up to this bonus.
DAILY_COIN_BASE = 3
DAILY_COIN_MAX_BONUS = 4

# "mock" = credit coins with no charge (local development only).
# Replace with a real gateway (Paystack / Flutterwave / Stripe) before launch.
PAYMENTS_MODE = env("PAYMENTS_MODE", "mock")
# PLACEHOLDER pricing. Set your real packs and prices.
COIN_PACKS = [
    {"code": "starter", "coins": 50, "price_label": "₦500"},
    {"code": "reader", "coins": 120, "price_label": "₦1,000"},
    {"code": "patron", "coins": 300, "price_label": "₦2,000"},
]

# PLACEHOLDER contract terms shown on the author benefits page. Replace with your real terms.
CONTRACT_OPTIONS = [
    {
        "code": "exclusive",
        "name": "Exclusive",
        "share": 70,
        "summary": "Your story is published only on InkHobby, and in return we put our full weight behind it.",
        "perks": [
            "Highest revenue share on every unlocked chapter",
            "Priority placement on the homepage and genre shelves",
            "Editorial attention and first access to our editor and proofreader network",
        ],
    },
    {
        "code": "non_exclusive",
        "name": "Non-exclusive",
        "share": 50,
        "summary": "Publish here and anywhere else you like, and keep full control of your rights.",
        "perks": [
            "Earn from every chapter your readers unlock",
            "Keep publishing on other platforms",
            "Upgrade to an exclusive contract whenever your story is ready",
        ],
    },
]

# Languages offered in the reader's translation menu (Google Cloud Translation codes).
TRANSLATION_LANGUAGES = [
    ("fr", "Français"), ("es", "Español"), ("pt", "Português"), ("de", "Deutsch"),
    ("it", "Italiano"), ("nl", "Nederlands"), ("ru", "Русский"), ("tr", "Türkçe"),
    ("ar", "العربية"), ("hi", "हिन्दी"), ("bn", "বাংলা"), ("ur", "اردو"),
    ("zh-CN", "中文（简体）"), ("ja", "日本語"), ("ko", "한국어"), ("id", "Bahasa Indonesia"),
    ("vi", "Tiếng Việt"), ("th", "ไทย"), ("tl", "Filipino"), ("sw", "Kiswahili"),
    ("yo", "Yorùbá"), ("ig", "Igbo"), ("ha", "Hausa"), ("zu", "isiZulu"),
    ("am", "አማርኛ"), ("pl", "Polski"), ("uk", "Українська"), ("el", "Ελληνικά"),
]
GOOGLE_TRANSLATE_API_KEY = env("GOOGLE_TRANSLATE_API_KEY")
