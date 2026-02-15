import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key')

def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


DEBUG = _env_bool("DEBUG", default=True)

def _env_csv(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [part.strip() for part in value.split(",") if part.strip()]


def _dedupe_csv(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        output.append(value)
        seen.add(value)
    return output


_render_external_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
RENDER_EXTERNAL_HOSTNAME = _render_external_hostname

_default_allowed_hosts = ["localhost", "127.0.0.1", "[::1]"]
_allowed_hosts = _env_csv("ALLOWED_HOSTS")
if _render_external_hostname:
    _allowed_hosts.append(_render_external_hostname)

ALLOWED_HOSTS = _dedupe_csv(_allowed_hosts) or _default_allowed_hosts

_csrf_trusted_origins = _env_csv("CSRF_TRUSTED_ORIGINS")
if _render_external_hostname:
    _csrf_trusted_origins.append(f"https://{_render_external_hostname}")

CSRF_TRUSTED_ORIGINS = _dedupe_csv(_csrf_trusted_origins)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Applications tierces
    'crispy_forms',
    'crispy_bootstrap5',
    # Applications locales
    'voitures.apps.VoituresConfig',
]

AUTHENTICATION_BACKENDS = [
    "voitures.auth_backends.UsernameOrEmailBackend",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'voitures.context_processors.notification_counts',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}
REQUIRE_POSTGRES = _env_bool("REQUIRE_POSTGRES", default=False)
if REQUIRE_POSTGRES and "sqlite3" in DATABASES["default"]["ENGINE"]:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured(
        "PostgreSQL requis: définissez DATABASE_URL vers une base Postgres (ex: postgres://...)."
    )

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

if "test" in sys.argv:
    STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Projet académique / démos: on sert les médias via Django/Gunicorn par défaut.
# Désactivez via SERVE_MEDIA=false si vous servez MEDIA_URL autrement (Nginx, stockage externe, etc.).
SERVE_MEDIA = _env_bool("SERVE_MEDIA", default=True)

# Dossier (dans le repo) qui contient un "catalogue" de logos de marques.
# Utilisé comme fallback si `Marque.logo` n'est pas défini.
BRAND_LOGO_CATALOG_DIR = BASE_DIR / "logo"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuration de crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# URL de redirection après connexion
LOGIN_REDIRECT_URL = 'accueil'
LOGOUT_REDIRECT_URL = 'accueil'
LOGIN_URL = 'connexion'

# Réservations / transactions
# Durée max (en heures) d'une transaction "en_attente" avant annulation automatique.
RESERVATION_TTL_HOURS = int(os.getenv("RESERVATION_TTL_HOURS", "24"))

# Paramètres de sécurité (activés en production uniquement)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Email (réinitialisation mot de passe)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@automarket.local")
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
