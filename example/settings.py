DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Harry Marr', 'harry.marr@gmail.com'),
)

MANAGERS = ADMINS

import os
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

import mongoengine
mongoengine.connect('mumblr-example')

TIME_ZONE = 'Europe/London'
LANGUAGE_CODE = 'en-gb'
#SITE_ID = 1
USE_I18N = False

MEDIA_ROOT = os.path.join(PROJECT_PATH, 'static')
MEDIA_URL = '/static/'

SECRET_KEY = '$geoon8_ymg-k)!9wl3wloq4&30w$rhc1*zv%h6m_&nza(4)nk'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.media',
    'mumblr.context_processors.auth',
    'mumblr.context_processors.csrf',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'mumblr.middleware.CsrfMiddleware',
    'mumblr.middleware.AuthMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'mongoengine.django.auth.MongoEngineBackend',
)

ROOT_URLCONF = 'example.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = (
    'typogrify',
    'signed',
    'mumblr',
)

LOGIN_URL = '/admin/login/'

TEST_RUNNER = 'testrunner.run_tests'

MUMBLR_MARKUP_LANGUAGE = 'markdown'
