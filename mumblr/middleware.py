from django.conf import settings
from django.utils.hashcompat import md5_constructor
from django.utils.cache import patch_vary_headers

from signed.signed import unsign
from random import randrange
from mongoengine.django.auth import get_user


class AuthMiddleware(object):
    """Middleware that tacks a User object on to the request object by fetching
    the user with the username specified in a signed cookie. The standard
    AuthMiddleware depends on sessions, which is why this is necessary.
    """
    
    def process_request(self, request):
        userid = None
        try:
            userid = unsign(request.COOKIES['userid'])
        except:
            pass
        request.user = get_user(userid)


if not getattr(settings, 'CSRF_COOKIE_NAME', None):
    settings.CSRF_COOKIE_NAME = 'csrftoken'

def _get_new_csrf_token():
    return md5_constructor('%s%s' % (randrange(0, 100000), 
                                     settings.SECRET_KEY)).hexdigest()


class CsrfMiddleware(object):
    """Middleware to protect pages against CSRF attacks using cookies. This
    is necessary until Django 1.2 is released, which includes a new CSRF
    framework allows sessions to be bypassed.
    """
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        try:
            token = request.COOKIES[settings.CSRF_COOKIE_NAME]
        except:
            token = _get_new_csrf_token()
        request.META['CSRF_COOKIE'] = token

    def process_response(self, request, response):
        cookie = request.META.get('CSRF_COOKIE')
        if cookie:
            response.set_cookie(settings.CSRF_COOKIE_NAME,
                                request.META['CSRF_COOKIE'], 
                                max_age=60 * 60 * 24 * 52)
            patch_vary_headers(response, ('Cookie',))
        return response
