from modarchive.settings.base import *
from datetime import datetime

DEBUG = False

DATABASES['legacy'] = {
    'ENGINE': 'django.db.backends.mysql',
    'HOST': os.getenv('MYSQL_HOST', 'localhost'),
    'NAME': os.getenv('MYSQL_DATABASE_NAME', 'tma'),
    'USER': os.getenv('MYSQL_USERNAME'),
    'PASSWORD': os.getenv('MYSQL_PASSWORD'),
    'PORT': os.getenv('MYSQL_PORT', '3306')
}

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MAIN_ARCHIVE_DIR = os.getenv('MAIN_ARCHIVE_DIR')
TEMP_UPLOAD_DIR = os.getenv('TEMP_UPLOAD_DIR')
NEW_FILE_DIR = os.getenv('NEW_FILE_DIR')
REJECTED_FILE_DIR = os.getenv('REJECTED_FILE_DIR')
REMOVED_FILE_DIR = os.getenv('REMOVED_FILE_DIR')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(
                os.getenv('LOG_DIR'),
                f"app-{datetime.now().strftime('%Y-%m-%d')}.log"
            ),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'modarchive': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}