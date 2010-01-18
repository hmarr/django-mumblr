from django.conf import settings

def auth(request):
    if hasattr(request, 'user'):
        return {'user': request.user}
    return {}

def csrf(request):
    return {'csrf_token': request.META['CSRF_COOKIE']}

def site_info(context):
    return {
        'SITE_INFO_TITLE': settings.SITE_INFO_TITLE or "Mumblr",
        'SITE_INFO_DESC': settings.SITE_INFO_DESC or "Simple blogging.",
    }
