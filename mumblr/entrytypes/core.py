from django import forms
from django.conf import settings

from mongoengine import *

from mumblr.entrytypes import EntryType


MARKUP_LANGUAGE = getattr(settings, 'MUMBLR_MARKUP_LANGUAGE', None)

def markup(text):
    """Markup text using the markup language specified in the settings.
    """
    if MARKUP_LANGUAGE == 'markdown':
        import markdown
        try:
            import pygments
            return markdown.markdown(text, ['codehilite'])
        except ImportError:
            return markdown.markdown(text)
    return text


class HtmlEntry(EntryType):
    """An HTML-based entry, which will be converted from the markup language
    specified in the settings.
    """
    content = StringField(required=True)
    rendered_content = StringField(required=True)

    type = 'HTML'

    def save(self):
        """Convert any markup to HTML before saving.
        """
        self.rendered_content = markup(self.content)
        super(HtmlEntry, self).save()

    class AdminForm(EntryType.AdminForm):
        content = forms.CharField(widget=forms.Textarea)


class LinkEntry(EntryType):
    """A link-based entry - the title is a link to the specified url and the
    content is the optional description.
    """
    link_url = StringField(required=True)
    description = StringField()

    type = 'Link'

    def rendered_content(self):
        if self.description:
            return markup(self.description)
        return '<p>Link: <a href="%s">%s</a></p>' % (self.link_url, 
                                                     self.link_url)

    class AdminForm(EntryType.AdminForm):
        link_url = forms.URLField()
        description = forms.CharField(widget=forms.Textarea, required=False)


class ImageEntry(EntryType):
    """An image-based entry - displays the image at the given url along with
    the optional description.
    """
    image_url = StringField(required=True)
    description = StringField()

    type = 'Image'

    def rendered_content(self):
        url = self.image_url
        if self.local:
            url = settings.MEDIA_URL + self.image_url
        html = '<img src="%s" />' % url
        if self.description:
            html += markup(self.description)
        return html

    class AdminForm(EntryType.AdminForm):
        image_url = forms.URLField()
        description = forms.CharField(widget=forms.Textarea, required=False)


EntryType.register(HtmlEntry)
EntryType.register(LinkEntry)
EntryType.register(ImageEntry)
