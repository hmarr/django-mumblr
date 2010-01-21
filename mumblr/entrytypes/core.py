import re
from django import forms

from mongoengine import *

from mumblr.entrytypes import EntryType, Comment, markup


class HtmlComment(Comment):
    """An HTML-based entry, which will be converted from the markup language
    specified in the settings.
    """
    rendered_content = StringField(required=True)


class TextEntry(EntryType):
    """An HTML-based entry, which will be converted from the markup language
    specified in the settings.
    """
    content = StringField(required=True)
    rendered_content = StringField(required=True)

    type = 'Text'

    def save(self):
        """Convert any markup to HTML before saving.
        """
        self.rendered_content = markup(self.content)
        super(TextEntry, self).save()

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
        html = '<img src="%s" />' % url
        if self.description:
            html += markup(self.description)
        return html

    class AdminForm(EntryType.AdminForm):
        image_url = forms.URLField()
        description = forms.CharField(widget=forms.Textarea, required=False)


class VideoEntry(EntryType):
    """An video-based entry - will try to embed the video if it is of
    and known type e.g. YouTube
    """
    video_url = StringField(required=True)
    description = StringField()

    type = 'Video'

    embed_codes = {
        'vimeo': (
            '<object width="600" height="338"><param name="allowfullscr'
            'een" value="true" /><param name="allowscriptaccess" value='
            '"always" /><param name="movie" value="http://vimeo.com/moo'
            'galoop.swf?clip_id={{!ID}}&amp;server=vimeo.com&amp;show_t'
            'itle=0&amp;show_byline=0&amp;show_portrait=0&amp;color=59a'
            '5d1&amp;fullscreen=1" /><embed src="http://vimeo.com/mooga'
            'loop.swf?clip_id=8833777&amp;server=vimeo.com&amp;show_tit'
            'le=0&amp;show_byline=0&amp;show_portrait=0&amp;color=59a5d'
            '1&amp;fullscreen=1" type="application/x-shockwave-flash" a'
            'llowfullscreen="true" allowscriptaccess="always" width="60'
            '0" height="338"></embed></object>'
        ),
        'youtube': (
            '<object width="600" height="361">'
            '<param name="movie" value="{{!ID}}"></param>'
            '<param name="allowFullScreen" value="true"></param>'
            '<param name="allowscriptaccess" value="always"></param>'
            '<embed src="http://www.youtube.com/v/{{!ID}}&fs=1&rel=&'
            'hd=10&showinfo=0type="application/x-shockwave-flash" '
            'allowscriptaccess="always" allowfullscreen="true" '
            'width="600" height="361"></embed></object>'
        )
    }

    embed_patterns = (
        ('youtube', r'youtube\.com\/watch\?v=([A-Za-z0-9._%-]+)[&\w;=\+_\-]*'),
        ('vimeo', r'vimeo\.com\/(\d+)'),
    )

    def rendered_content(self):
        video_url = self.video_url
        for source, pattern in VideoEntry.embed_patterns:
            id = re.findall(pattern, video_url)
            if id:
                embed = VideoEntry.embed_codes[source]
                html = embed.replace('{{!ID}}', id[0])
                break
        else:
            html = 'Video: <a href="video_url">%s</a>' % video_url

        if self.description:
            html += markup(self.description)
        return html

    class AdminForm(EntryType.AdminForm):
        video_url = forms.URLField()
        description = forms.CharField(widget=forms.Textarea, required=False)


EntryType.register(TextEntry)
EntryType.register(LinkEntry)
EntryType.register(ImageEntry)
EntryType.register(VideoEntry)
