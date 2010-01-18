import mongoengine
mongoengine.connect('mumblr-example')

import os
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT = os.path.join(PROJECT_PATH, '..', 'mumblr', 'static')

SECRET_KEY = '$geoon8_ymg-k)!9wl3wloq4&30w$rhc1*zv%h6m_&nza(4)nk'

RECAPTCHA_PUBLIC_KEY = "6LfFgQoAAAAAABQTj4YjuPbccgKtZStoiWtr7E5k"
RECAPTCHA_PRIVATE_KEY = "6LfFgQoAAAAAAM-0SAUTe7WxZ-thnWFfSpoc7sfJ"

