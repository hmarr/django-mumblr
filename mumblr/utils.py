from django.http import HttpResponseForbidden
from django.conf import settings

def csrf_protect(*methods):
    """Decorator that protects a view from CSRF attacks. Specify all HTTP
    methods that need protection as positional arguments.
    """
    methods = [method.lower() for method in methods]
    def decorator(func):
        def protected_func(request, *args, **kwargs):
            # token is the csrf token currently in use, probably from a cookie
            token = request.META['CSRF_COOKIE']
            token_name = settings.CSRF_COOKIE_NAME

            client_token = None
            protect = False
            if request.method == 'POST' and request.method.lower() in methods:
                client_token = request.POST.get(token_name, None)
                protect = True
            elif request.method.lower() in methods:
                client_token = request.GET.get(token_name, None)
                protect = True

            if protect and token != client_token:
                return HttpResponseForbidden('Forbidden')
            return func(request, *args, **kwargs)
        return protected_func
    return decorator
