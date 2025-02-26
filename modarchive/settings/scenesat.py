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