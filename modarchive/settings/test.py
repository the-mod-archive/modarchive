from modarchive.settings.base import *
import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', '')

ALLOWED_HOSTS = ['127.0.0.1', '.herokuapp.com']

INSTALLED_APPS = list(INSTALLED_APPS) + [
    'whitenoise.runserver_nostatic'
]

MIDDLEWARE = list(MIDDLEWARE) + [
    'whitenoise.middleware.WhiteNoiseMiddleware'
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Database settings
db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('MAILGUN_SMTP_SERVER', '')
EMAIL_PORT = os.getenv('MAILGUN_SMTP_PORT', '')
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('MAILGUN_SMTP_LOGIN', '')
EMAIL_HOST_PASSWORD = os.getenv('MAILGUN_SMTP_PASSWORD', '')

BASE_URL = "https://modarchive-test.herokuapp.com"