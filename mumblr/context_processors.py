from django.conf import settings

def auth(request):
    if hasattr(request, 'user'):
        return {'user': request.user}
    return {}

def site_info(context):
    title = getattr(settings, 'SITE_INFO_TITLE', None)
    description = getattr(settings, 'SITE_INFO_DESC', None)
    return {
        'SITE_INFO_TITLE': title or 'Mumblr', 
        'SITE_INFO_DESC': description or 'Simple Blogging.',
    }
