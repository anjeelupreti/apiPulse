# stuff every environment needs. dev.py / prod.py both import * from this,
# then override the bits that actually differ (DEBUG, ALLOWED_HOSTS, etc)

import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# this file is backend/config/settings/base.py, so I need 3 parents to get
# back up to backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / '.env')

# so I can write INSTALLED_APPS as 'monitors' instead of 'apps.monitors'
# everywhere — apps/ isn't a real package, just a folder I dump my apps in
sys.path.append(str(BASE_DIR / 'apps'))


# SECURITY WARNING: keep the secret key used in production secret!
# falls back to this insecure key so dev.py works without me needing a .env
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 'django-insecure-ccs!@o*2h-8x@xx%c%c0%+s++&op$9z1gz348sz3ixtf5i^8cy'
)

# DEBUG / ALLOWED_HOSTS differ per environment -> those live in dev.py / prod.py


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
]

LOCAL_APPS = [
    'accounts',
    'monitors',
    'checks',
    'incidents',
    'alerts',
    'flags',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
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
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# same engine everywhere (Postgres, in dev too — decided against sqlite
# since the diagram I drew up already assumed Postgres). only the host/creds
# change per environment, and those come from .env, not from here

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'pulsewatch'),
        'USER': os.environ.get('DB_USER', 'pulsewatch'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'pulsewatch'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework
# https://www.django-rest-framework.org/api-guide/settings/

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # JWT is what the frontend will actually use to log in. Keeping
        # session + basic around too — session so the browsable API/admin
        # login still works, basic so I can keep testing with plain curl
        # without minting a token first.
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
}

# defaults are an hour/day, which is fine for now — just being explicit
# about it here instead of relying on simplejwt's built-in defaults
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Google login. Only the Client ID is actually used - we verify the ID
# token the frontend gets from Google's Identity Services JS, we don't do
# the server-side auth-code exchange (that's the flow that needs the
# secret + a redirect URI, and it's more machinery than an SPA needs).
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')

# Key for encrypting monitor auth credentials (API keys/tokens/basic auth
# a user gives us so we can ping their protected endpoints) at rest in
# Postgres. Generate with: python -c "from cryptography.fernet import
# Fernet; print(Fernet.generate_key().decode())" - a fresh one per
# environment. Losing this key means every stored credential becomes
# unrecoverable garbage, so treat it like any other production secret.
FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY', '')


# Celery — Redis is doing double duty here, it's both the task queue
# (broker) and where task results get stashed (result backend)

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# just one entry that fires every 15s — dispatch_due_checks figures out
# *which* monitors are actually due on its own, so I don't have to touch
# this schedule every time I add or remove a monitor
CELERY_BEAT_SCHEDULE = {
    'dispatch-due-checks': {
        'task': 'monitors.tasks.dispatch_due_checks',
        'schedule': 15.0,
    },
}


# Email — using plain Gmail SMTP for now (an app password, not my real
# Gmail password — Google requires those for SMTP once 2FA is on). Fine
# for getting alerts working; I'll move to a real transactional email
# service (SES, Postmark, whatever) before this is anything but my own dev.

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
