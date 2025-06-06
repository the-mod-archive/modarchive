import tempfile
from modarchive.settings.base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

IS_RECAPTCHA_ENABLED = False

BASE_URL = 'http://localhost:8000'

TEMP_UPLOAD_DIR = tempfile.mkdtemp(prefix='temp_uploads_')
NEW_FILE_DIR = tempfile.mkdtemp(prefix='new_files_')
MAIN_ARCHIVE_DIR = tempfile.mkdtemp(prefix='main_archive_')
REJECTED_FILE_DIR = tempfile.mkdtemp(prefix='rejected_files_')
REMOVED_FILE_DIR = tempfile.mkdtemp(prefix='removed_files_')
