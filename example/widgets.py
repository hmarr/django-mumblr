from django import forms
from django.utils.safestring import mark_safe
from django.conf import settings
import captcha

class ReCaptcha(forms.widgets.Widget):
    """Renders the proper ReCaptcha widget
    """
    def render(self, name, value, attrs=None):
        html = captcha.displayhtml(settings.RECAPTCHA_PUBLIC_KEY)
        return mark_safe(u'%s' % html)

    def value_from_datadict(self, data, files, name):
        return [data.get('recaptcha_challenge_field', None), 
                data.get('recaptcha_response_field', None)]

