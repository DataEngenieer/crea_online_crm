import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-por-defecto-cambiar-en-produccion')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'
#DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,crea_online_crm.up.railway.app').split(',')

# Configuración para entornos de producción
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    # Asegurarse de que no haya redirecciones a HTTPS en desarrollo
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = None


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'core',
    'tickets',
    'widget_tweaks',  # Añadido aquí
    'crispy_forms', # Añadido para Crispy Forms
    'crispy_bootstrap5', # Añadido para el paquete Bootstrap 5 de Crispy Forms
    'chat',
    'telefonica',
    'calidad',  # Módulo de Calidad agregado
    'tarjeta_plata',  # Módulo de Tarjeta Plata agregado
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.LoginRequiredMiddleware',  # Middleware personalizado para requerir login
    'telefonica.middleware.TelefonicaMenuMiddleware',  # Middleware para el menú de Telefónica
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'crea_online_crm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates', BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'telefonica.context_processors.telefonica_menu',  # Contexto para menú de Telefónica
            ],
        },
    },
]

WSGI_APPLICATION = 'crea_online_crm.wsgi.application'



# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/db.sqlite3'),
        conn_max_age=600
    )
}

# Deshabilitar cursores del lado del servidor para evitar errores de 'InvalidCursorName'
# Esto soluciona el error: cursor "_django_curs_XXXXX" does not exist
DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-co'  # Español de Colombia

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = []
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# Archivos multimedia

MEDIA_URL = '/media/'
# Configuración de la ruta para los archivos multimedia, usando una variable de entorno
# para la ruta base en producción (ej. el volumen de Railway en /data/media)
MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Expiración de sesión: 12 horas (43200 segundos)
SESSION_COOKIE_AGE = 43200  # 12 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Nombre único para la cookie de sesión para evitar conflictos con otras aplicaciones Django
SESSION_COOKIE_NAME = 'crea_online_crm_sessionid'

# Configuración de correo electrónico (usando variables de entorno)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = os.getenv('EMAIL_PORT', 587)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Configuración de logging
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
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configuración de login/logout
LOGIN_URL = 'core:login'
LOGIN_REDIRECT_URL = 'core:inicio'
LOGOUT_REDIRECT_URL = 'core:login'

# Configuraciones para django-crispy-forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# --- Depuración de variables de entorno en producción ---
# Imprime los valores en los logs para verificar que se están leyendo correctamente.
# Configuración de MinIO
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', '')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', '')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', '')
#MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'default-bucket')

MINIO_BUCKET_NAME = {
"MINIO_BUCKET_NAME_LLAMADAS":"llamadas-crea-online",
"MINIO_BUCKET_NAME_TRANSCRIPCIONES":"transcripciones-crea-online",
"MINIO_BUCKET_NAME_TICKET":"tickets-crea-online",
"MINIO_BUCKET_NAME_TELEFONICA":"telefonica-crea-online",
"MINIO_BUCKET_NAME_TARJETA_PLATA":"tarjeta-plata-crea-online"
}


import sys
print(f"[DJANGO-SETTINGS] DEBUG = {DEBUG}", file=sys.stderr)
print(f"[DJANGO-SETTINGS] MEDIA_ROOT = {MEDIA_ROOT}", file=sys.stderr)
print(f"[DJANGO-SETTINGS] ALLOWED_HOSTS = {ALLOWED_HOSTS}", file=sys.stderr)
# --- Fin de la depuración ---
