from django import template
from django.utils.safestring import mark_safe
from django.conf import settings


class CsrfFormTokenNode(template.Node):

    def render(self, context):
        token = context.get('csrf_token', None)
        if token:
            token_name = settings.CSRF_COOKIE_NAME
            field = '<input type="hidden" name="%s" value="%s" />' 
            return mark_safe(field % (token_name, token))
        else:
            return mark_safe('<!-- NO CSRF TOKEN IN CONTEXT -->')


class CsrfUrlTokenNode(template.Node):

    def render(self, context):
        token = context.get('csrf_token', None)
        if token:
            param = '%s=%s' % (settings.CSRF_COOKIE_NAME, token)
            return mark_safe(param)
        else:
            return mark_safe('csrf_token=NO_TOKEN_IN_CONTEXT')


register = template.Library()

def csrf_form_token(parser, token):
    """Template tag that renders a hidden form tag with the CSRF token.
    """
    return CsrfFormTokenNode()
register.tag(csrf_form_token)

def csrf_url_token(parser, token):
    """Template tag that renders the CSRF token as a GET parameter for a URL.
    """
    return CsrfUrlTokenNode()
register.tag(csrf_url_token)
