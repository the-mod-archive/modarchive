from modarchive.settings.base import *
import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', '.herokuapp.com']

INSTALLED_APPS = list(INSTALLED_APPS) + [
    'whitenoise.runserver_nostatic'
]

MIDDLEWARE = list(MIDDLEWARE) + [
    'whitenoise.middleware.WhiteNoiseMiddleware'
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'localhost',
        'NAME': 'mod_archive',
        'USER': 'postgres',
        'PASSWORD': 'docker',
        'PORT': '5432'
    }
}

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)