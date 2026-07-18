"""
settings.py — configurazione centrale del progetto BiblioLab.

Django legge questo file all avvio per sapere:
- dove si trova il database
- quali app sono installate
- come si trovano i template
- come si servono i file statici

Questo file funziona sia in sviluppo (SQLite, DEBUG=True)
che in produzione (PostgreSQL, DEBUG=False) usando variabili d ambiente.
"""

import os  # per leggere le variabili d ambiente con os.environ.get()
from pathlib import Path  # per costruire percorsi cross-platform (Windows/Linux/Mac)

# BASE_DIR: percorso assoluto della cartella radice del progetto.
# __file__ e il percorso di questo file (settings.py).
# .resolve() lo rende assoluto eliminando symlink.
# .parent.parent risale due livelli: settings.py -> bibliolab/ -> radice progetto.
BASE_DIR = Path(__file__).resolve().parent.parent

# ── SICUREZZA ─────────────────────────────────────────────────────────────────

# SECRET_KEY firma cookie, sessioni e token CSRF.
# In produzione deve essere una stringa lunga e casuale, mai nel codice sorgente.
# os.environ.get legge dalla variabile d ambiente; il secondo argomento e il default.
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-bibliolab-corso-arces-palermo-cambiare-in-produzione"
)

# DEBUG=True mostra stack trace agli utenti (utile in sviluppo, pericoloso in produzione).
# La variabile d'ambiente è una stringa, quindi confrontiamo con la stringa 'True'.
DEBUG = os.environ.get("DEBUG", "True") == "True"

# ALLOWED_HOSTS: domini da cui Django accetta richieste.
# Con DEBUG=True Django accetta tutto; con DEBUG=False questa lista e obbligatoria.
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:5173")

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# In fondo a settings.py, dopo CORS_ALLOWED_ORIGINS
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_PREFLIGHT_MAX_AGE = 86400  # 24 ore

CSRF_TRUSTED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"] # for csrf token to be safe
# ── APP INSTALLATE ────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    # App built-in di Django:
    "corsheaders",  # aggiunto per accedere ad localhost:5173
    "django.contrib.admin",  # pannello admin automatico (/admin/)
    "django.contrib.auth",  # autenticazione: User, login, logout, permessi
    "django.contrib.contenttypes",  # framework per relazioni generiche tra Model
    "django.contrib.sessions",  # sessioni utente lato server
    "django.contrib.messages",  # messaggi flash (success, error, warning...)
    "django.contrib.staticfiles",  # gestione e serving dei file statici
    # Terze parti:
    "rest_framework",  # Django REST Framework per le API JSON
    # Nostre app:
    "catalogo",  # app principale di BiblioLab
    "accounts", # authorization app for frontend frameworks
    
]

# ── MIDDLEWARE ────────────────────────────────────────────────────────────────

# I middleware elaborano ogni richiesta/risposta in sequenza.
# L ordine e importante: la richiesta segue l ordine scritto,
# la risposta segue l ordine inverso.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",  # header HTTP di sicurezza
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # file statici in produzione (subito dopo Security)
    "django.contrib.sessions.middleware.SessionMiddleware",  # abilita le sessioni
    "django.middleware.common.CommonMiddleware",  # trailing slash, Content-Length...
    "django.middleware.csrf.CsrfViewMiddleware",  # protezione CSRF sui form POST
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # collega request.user all utente
    "django.contrib.messages.middleware.MessageMiddleware",  # messaggi flash
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # protezione clickjacking
]

# ROOT_URLCONF: dove si trova la rubrica principale degli URL del progetto.
ROOT_URLCONF = "bibliolab.urls"

# ── TEMPLATE ──────────────────────────────────────────────────────────────────

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # DIRS: cartelle aggiuntive per i template globali (base.html, login.html...).
        "DIRS": [BASE_DIR / "templates"],
        # APP_DIRS=True: cerca template anche in ogni app (catalogo/templates/).
        "APP_DIRS": True,
        "OPTIONS": {
            # context_processors aggiungono variabili automatiche ad ogni template.
            "context_processors": [
                "django.template.context_processors.debug",  # variabile {{ debug }}
                "django.template.context_processors.request",  # variabile {{ request }}
                "django.contrib.auth.context_processors.auth",  # variabili {{ user }}, {{ perms }}
                "django.contrib.messages.context_processors.messages",  # variabile {{ messages }}
            ],
        },
    },
]

# WSGI_APPLICATION: applicazione WSGI usata da Gunicorn in produzione.
WSGI_APPLICATION = "bibliolab.wsgi.application"

# ── DATABASE ──────────────────────────────────────────────────────────────────

# In produzione (Docker) si usa DATABASE_URL (es. postgres://user:pass@db:5432/bibliolab).
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    # Produzione: PostgreSQL via DATABASE_URL.
    # dj_database_url.parse() converte la stringa URL nel dizionario che Django si aspetta.
    import dj_database_url

    DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}
else:
    # Sviluppo: SQLite — file singolo, zero configurazione.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",  # backend SQLite integrato in Python
            "NAME": BASE_DIR / "db.sqlite3",  # file creato nella radice del progetto
        }
    }

# ── VALIDAZIONE PASSWORD ──────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },  # no password simile all username
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"
    },  # minimo 8 caratteri
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },  # no password comuni
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },  # no solo numeri
]

# ── LOCALIZZAZIONE ────────────────────────────────────────────────────────────

LANGUAGE_CODE = "it-it"  # lingua Admin e messaggi di errore
TIME_ZONE = "Europe/Rome"  # fuso orario per date/ore nel database
USE_I18N = True  # abilita le traduzioni
USE_TZ = True  # usa datetime con fuso orario (timezone-aware)

# ── FILE STATICI ──────────────────────────────────────────────────────────────

STATIC_URL = "/static/"  # URL base per i file statici nel browser
STATICFILES_DIRS = [BASE_DIR / "static"]  # cartelle statici globali del progetto
STATIC_ROOT = (
    BASE_DIR / "staticfiles"
)  # destinazione di collectstatic (produzione cartella creata da collectstatic)

# Whitenoise: serve i file statici con compressione gzip e hash nel nome per il caching.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ── FILE MEDIA ────────────────────────────────────────────────────────────────

MEDIA_URL = "/media/"  # URL per i file caricati dagli utenti
MEDIA_ROOT = BASE_DIR / "media"  # cartella fisica per i file caricati

# ── CHIAVE PRIMARIA DEFAULT ───────────────────────────────────────────────────

# BigAutoField = intero a 64 bit — evita overflow su tabelle con molti record.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── AUTENTICAZIONE ────────────────────────────────────────────────────────────

LOGIN_URL = "/accounts/login/"  # redirect se si accede a View protette senza login
LOGIN_REDIRECT_URL = "/"  # redirect dopo login riuscito
LOGOUT_REDIRECT_URL = "/"  # redirect dopo logout

# ── DJANGO REST FRAMEWORK ─────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        # Lettura libera per tutti; scrittura solo per utenti autenticati.
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    # Paginazione automatica: 10 oggetti per pagina.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ── MESSAGGI FLASH ────────────────────────────────────────────────────────────

# Django usa il tag 'error' ma Bootstrap vuole 'danger' per il colore rosso degli alert.
from django.contrib.messages import constants as messages_constants

MESSAGE_TAGS = {
    messages_constants.ERROR: "danger",  # messages.error() -> classe CSS 'alert-danger'
}
