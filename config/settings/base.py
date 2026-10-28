import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('SECRET_KEY', 'unsafe-default-key')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# 1. ALLOWED_HOSTS: Add your laptop's local IP so it accepts requests from the network
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.5.5', '0.0.0.0']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'corsheaders',
    'drf_spectacular',

    # Local apps
    'core',
    'apps.users',
    'apps.accounts',
    'apps.farms',
    'apps.catalog',
    'apps.transactions',
    'apps.operations',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Keep first: must run before anything that can return a response
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# 2. CORS CONFIGURATION
# Allow the frontend origins (5500 = VS Code Live Server / python http.server)
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.5.8:3000",
    "http://192.168.5.8:5173",
]

# 3. CRITICAL for Session/Cookie Authentication across different origins
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

CSRF_COOKIE_HTTPONLY = False   # JS must be able to read csrftoken

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    # Point 6: Consistent pagination and ordering
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.OrderingFilter',
    ),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Farm Management Platform API',
    'DESCRIPTION': 'Initial focus: Layer poultry and egg production',
    'VERSION': '1.0.0',
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CRITICAL: Custom User Model (Must be set before first migration)
AUTH_USER_MODEL = 'users.User'