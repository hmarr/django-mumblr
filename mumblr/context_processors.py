from signed.signed import unsign

def auth(request):
    if hasattr(request, 'user'):
        return {'user': request.user}
    return {}

def csrf(request):
    return {'csrf_token': request.META['CSRF_COOKIE']}
