from modarchive.settings.base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

IS_RECAPTCHA_ENABLED = False