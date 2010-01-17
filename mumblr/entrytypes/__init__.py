from django import forms
from django.conf import settings
from django.db.models import permalink
from django.forms.extras.widgets import SelectDateWidget
import fields

from datetime import datetime
import re
from uuid import uuid4
from mongoengine import *
from mongoengine.django.auth import User


MARKUP_LANGUAGE = getattr(settings, 'MUMBLR_MARKUP_LANGUAGE', None)

def markup(text, small_headings=False, no_follow=True):
    """Markup text using the markup language specified in the settings.
    """
    if MARKUP_LANGUAGE == 'markdown':
        import markdown
        try:
            import pygments
            text = markdown.markdown(text, ['codehilite'], safe_mode="escape")
        except ImportError:
            text = markdown.markdown(text, safe_mode="escape")
    
    if small_headings:
        text = re.sub('<(/?h)[1-6]', '<\g<1>5', text)

    if no_follow:
        text = re.sub('<a (?![^>]*nofollow)', '<a rel="nofollow" ', text)

    return text


class Comment(EmbeddedDocument):
    """A comment that may be embedded within a post.
    """
    id = StringField(required=True, default=uuid4)
    author = StringField()
    body = StringField()
    date = DateTimeField(required=True, default=datetime.now)
    is_admin = BooleanField(required=True, default=False)

    class CommentForm(forms.Form):

        author = forms.CharField()
        body = forms.CharField(widget=forms.Textarea)

        def __init__(self, user, *args, **kwargs):
            super(Comment.CommentForm, self).__init__(*args, **kwargs)
            if not user.is_authenticated():
                # Only show captcha for anonymous users
                recaptcha = fields.ReCaptchaField(label="Human?")
                self.fields['recaptcha'] = recaptcha
            else:
                # Initialise author field if user logged in
                author = "%s %s" % (user.first_name, user.last_name)
                self.fields['author'].initial = author


class EntryType(Document):
    """The base class for entry types. New types should inherit from this and
    extend it with relevant fields. You must define a method
    :meth:`EntryType.rendered_content`\ , which returns a string of HTML that
    will be used as the content. To make the entry's title link somewhere other
    than the post, you may provide a :attr:`link_url` field.

    New entry types should also specify a form to be used in the admin 
    interface. This is done by creating a subclass of 
    :class:`EntryType.AdminForm` (which must also be called AdminForm) as a
    class attribute.
    """
    title = StringField(required=True)
    slug = StringField(required=True, regex='[A-z0-9_-]+')
    author = ReferenceField(User)
    date = DateTimeField(required=True, default=datetime.now)
    tags = ListField(StringField(max_length=50))
    comments = ListField(EmbeddedDocumentField(Comment))
    comments_enabled = BooleanField(default=True)
    published = BooleanField(default=True)
    publish_date = DateTimeField(required=False, default=None)
    expiry_date = DateTimeField(required=False, default=None)
    link_url = StringField()

    meta = {
        'indexes': ['slug', '-date', 'tags'],
    }

    _types = {}

    @queryset_manager
    def live_entries(queryset):
        return queryset(# Is it published
                        Q(published=True) &
                        # Is it past publish date
                        (Q(publish_date__lte=datetime.now()) |
                         Q(publish_date=None)) &
                        # Is it earlier than expiry date
                        (Q(expiry_date__gt=datetime.now()) |
                         Q(expiry_date=None))
                        )

    @permalink
    def get_absolute_url(self):
        date = self.date.strftime('%Y/%b/%d').lower()
        return ('entry-detail', (date, self.slug))

    def rendered_content(self):
        raise NotImplementedError()

    def save(self):
        def convert_tag(tag):
            tag = tag.strip().lower().replace(' ', '-')
            return re.sub('[^a-z0-9_-]', '', tag)
        self.tags = [convert_tag(tag) for tag in self.tags]
        self.tags = [tag for tag in self.tags if tag.strip()]
        super(EntryType, self).save()

    class AdminForm(forms.Form):

        title = forms.CharField()
        slug = forms.CharField()
        tags = forms.CharField(required=False)
        published = forms.BooleanField(required=False)
        publish_date = forms.DateTimeField(
            widget=SelectDateWidget(required=False),
            required=False)
        expiry_date = forms.DateTimeField(
            widget=SelectDateWidget(required=False),
            required=False)
        comments_enabled = forms.BooleanField(required=False, label="Comments?")

    @classmethod
    def register(cls, entry_type):
        """Register an EntryType subclass.
        """
        cls._types[entry_type.type.lower()] = entry_type
