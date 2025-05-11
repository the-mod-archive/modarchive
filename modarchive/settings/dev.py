import tempfile
from modarchive.settings.base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

IS_RECAPTCHA_ENABLED = False

BASE_URL = 'http://localhost:8000'

TEMP_UPLOAD_DIR = os.getenv('TEMP_UPLOAD_DIR', tempfile.mkdtemp(prefix='temp_uploads_'))
NEW_FILE_DIR = os.getenv('NEW_FILE_DIR', tempfile.mkdtemp(prefix='new_files_'))
MAIN_ARCHIVE_DIR = os.getenv('MAIN_ARCHIVE_DIR', tempfile.mkdtemp(prefix='main_archive_'))
REJECTED_FILE_DIR = os.getenv('REJECTED_FILE_DIR', tempfile.mkdtemp(prefix='rejected_files_'))
REMOVED_FILE_DIR = os.getenv('REMOVED_FILE_DIR', tempfile.mkdtemp(prefix='removed_files_'))

DATABASES['legacy'] = {
    'ENGINE': 'django.db.backends.mysql',
    'HOST': '127.0.0.1',
    'NAME': 'mods_tma',
    'USER': 'modarchive_local',
    'PASSWORD': 'password23',
    'PORT': '3306'
}

DOWNLOAD_STRATEGY = 'redirect'

# LOGGING = {
#     'version': 1,
#     'filters': {
#         'require_debug_true': {
#             '()': 'django.utils.log.RequireDebugTrue',
#         }
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'filters': ['require_debug_true'],
#             'class': 'logging.StreamHandler',
#         }
#     },
#     'loggers': {
#         'django.db.backends': {
#             'level': 'DEBUG',
#             'handlers': ['console'],
#         }
#     }
# }
