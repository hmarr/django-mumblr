DEBUG = True
TEMPLATE_DEBUG = True

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
USE_I18N = False

MEDIA_ROOT = os.path.join(PROJECT_PATH, 'static')
MEDIA_URL = '/static/'

SECRET_KEY = '$geoon8_ymg-k)!9wl3wloq4&30w$rhc1*zv%h6m_&nza(4)nk'

RECAPTCHA_PUBLIC_KEY = "6LfFgQoAAAAAABQTj4YjuPbccgKtZStoiWtr7E5k"
RECAPTCHA_PRIVATE_KEY = "6LfFgQoAAAAAAM-0SAUTe7WxZ-thnWFfSpoc7sfJ"

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
    'mumblr.context_processors.csrf',
    'mumblr.context_processors.site_info',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'mumblr.middleware.CsrfMiddleware',
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
    'typogrify',
    'mumblr',
)

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'

TEST_RUNNER = 'testrunner.run_tests'

MUMBLR_MARKUP_LANGUAGE = 'markdown'
