from modarchive.settings.base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

IS_RECAPTCHA_ENABLED = False

BASE_URL = 'http://localhost:8000'

DATABASES['legacy'] = {
    'ENGINE': 'django.db.backends.mysql',
    'HOST': 'localhost',
    'NAME': 'mods_tma',
    'USER': 'modarchive_local',
    'PASSWORD': 'password23',
    'PORT': '3306'
}