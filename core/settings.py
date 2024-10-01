"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 4.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os, random, string
from pathlib import Path
from dotenv import load_dotenv
from str2bool import str2bool

load_dotenv()  # take environment variables from .env.

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
APP_SECRET = os.getenv('APP_SECRET')
APP_ID = os.getenv('APP_ID')
VERSION = os.getenv('VERSION')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY') or ''.join(random.choice( string.ascii_lowercase  ) for i in range( 32 ))

# Enable/Disable DEBUG Mode
DEBUG = str2bool(os.environ.get('DEBUG'))
#print(' DEBUG -> ' + str(DEBUG) ) 

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://localhost:5085', 'http://127.0.0.1:8000', 'https://tithehurst.co.zw/']

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:    
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition

INSTALLED_APPS = [
    'admin_soft.apps.AdminSoftDashboardConfig',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "home",
    "a_bot",
    "rest_framework",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

HOME_TEMPLATES = os.path.join(BASE_DIR, 'templates')

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [HOME_TEMPLATES],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DB_ENGINE   = os.getenv('DB_ENGINE'   , None)
DB_USERNAME = os.getenv('DB_USERNAME' , None)
DB_PASS     = os.getenv('DB_PASS'     , None)
DB_HOST     = os.getenv('DB_HOST'     , None)
DB_PORT     = os.getenv('DB_PORT'     , None)
DB_NAME     = os.getenv('DB_NAME'     , None)

# if DB_ENGINE and DB_NAME and DB_USERNAME:
DATABASES = { 
    'default': {
    'ENGINE'  : 'django.db.backends.mysql', 
    'NAME'    : 'customer_support',
    'USER'    : 'simon',
    'PASSWORD': 'simonmusabayana',
    'HOST'    : '198.12.221.104',
    'PORT'    : '3306',
    }, 
}
# else:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': 'db.sqlite3',
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Optional - set task soft and hard time limits to avoid long-running tasks:
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Harare"

USE_I18N = True

USE_TZ = True
MEDIA_URL = 'media/'
# DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_ROOT = BASE_DIR / 'media' 
    

# cloudinary_storage.storage.MediaCloudinaryStorage
# cloudinary_storage.storage.RawMediaCloudinaryStorage 
# cloudinary_storage.storage.VideoMediaCloudinaryStorage
# CLOUDINARY_STORAGE = {
#     'CLOUD_NAME': os.getenv('CLOUD_NAME'),
#     'API_KEY': os.getenv('CLOUD_API_KEY'),
#     'API_SECRET': os.getenv('CLOUD_API_SECRET'),
# }


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
) 

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
#if not DEBUG:

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = '/enlsupport'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'godfreytantswakandeya@gmail.com'
EMAIL_HOST_PASSWORD = 'ijst bamj jjra ckka'
EMAIL_TIMEOUT = 10 
