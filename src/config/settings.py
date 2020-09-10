import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'lc!!ifja*y-$qqfv9tpa4s(@d#l65$ao=xx5#0$^k7(rd$e&+y'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'false').lower() == 'true'

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'workshops',
    'oauth2_provider',
    'corsheaders',
    'mod_wsgi.server',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'config', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'workshops.contexts.portal',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "../data"))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DATA_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'config', 'static'),
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}


# User login page.

LOGIN_URL = 'login'
LOGOUT_URL = 'logout'

LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'index'

# Crisp form rendering.

CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Enable DEBUG mode when mod_wsgi-express debugging enabled.

if os.environ.get('MOD_WSGI_ENABLE_DEBUGGER'):
    DEBUG = True
    DEBUG_PROPAGATE_EXCEPTIONS = True

# Assorted configuration for CORS, CSP, OAuth etc.

CORS_ORIGIN_ALLOW_ALL = True

CSP_DEFAULT_SRC = ("'none'", )
CSP_STYLE_SRC = ("'self'", )
CSP_SCRIPT_SRC = ("'self'", )
CSP_IMG_SRC = ("'self'", "data:", "www.google-analytics.com",
        "www.googletagmanager.com")
CSP_FONT_SRC = ("'self'", )
CSP_FRAME_SRC = ("'self'", )
CSP_INCLUDE_NONCE_IN = ("script-src", )
CSP_FRAME_ANCESTORS = ("'self'", )

frame_ancestors = os.environ.get("FRAME_ANCESTORS", "")

if frame_ancestors:
    CSP_FRAME_ANCESTORS = frame_ancestors.split(',')
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = 'None'
    CSRF_COOKIE_SECURE = True

OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'

OAUTH2_PROVIDER = {
    'SCOPES': {
        'user:info': 'User information',
    },
}

AUTHENTICATION_BACKENDS = [
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend'
]

registration_type = os.environ.get("REGISTRATION_TYPE", "one-step")
enable_registration = os.environ.get("ENABLE_REGISTRATION", "true")

if registration_type == "one-step" and enable_registration == "true":
    REGISTRATION_OPEN = True
else:
    REGISTRATION_OPEN = False