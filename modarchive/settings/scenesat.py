from modarchive.settings.base import *

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
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": "/home/tma/modarchive/django_error.log",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}