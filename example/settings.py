DEBUG = True
TEMPLATE_DEBUG = True

ADMINS = (
    ('Harry Marr', 'harry.marr@gmail.com'),
)

MANAGERS = ADMINS

import os
from local_settings import *

TIME_ZONE = 'Europe/London'
LANGUAGE_CODE = 'en-gb'
USE_I18N = False

MEDIA_ROOT = os.path.join(PROJECT_PATH, 'static')
MEDIA_URL = '/static/'

SITE_INFO_TITLE = ""
SITE_INFO_DESC = ""

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.media',
    'mumblr.context_processors.auth',
    'mumblr.context_processors.site_info',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.csrf.middleware.CsrfMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'mongoengine.django.auth.MongoEngineBackend',
)

SESSION_ENGINE = 'mongoengine.django.sessions'

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.sessions',
    'mumblr',
    'mytheme',
)

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'

TEST_RUNNER = 'testrunner.run_tests'

MUMBLR_MARKUP_LANGUAGE = 'markdown'
#MUMBLR_THEME = 'mytheme'
