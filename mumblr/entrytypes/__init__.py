from django import forms
from django.conf import settings
from django.db.models import permalink
from django.forms.extras.widgets import SelectDateWidget
import fields

from datetime import datetime, date, timedelta
import re
from uuid import uuid4
from mongoengine import *
from mongoengine.django.auth import User


MARKUP_LANGUAGE = getattr(settings, 'MUMBLR_MARKUP_LANGUAGE', None)

def markup(text, small_headings=False, no_follow=True, escape=False):
    """Markup text using the markup language specified in the settings.
    """
    if MARKUP_LANGUAGE == 'markdown':
        import markdown
        safe_mode = 'escape' if escape else None
        try:
            import pygments
            text = markdown.markdown(text, ['codehilite', 'footnotes', 'abbr'],
                                     safe_mode=safe_mode)
        except ImportError:
            text = markdown.markdown(text, ['footnotes', 'abbr'],
                                     safe_mode=safe_mode)
    
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
    creation_date = DateTimeField(required=True, default=datetime.now)
    tags = ListField(StringField(max_length=50))
    comments = ListField(EmbeddedDocumentField(Comment))
    comments_enabled = BooleanField(default=True)
    comments_expiry = StringField(required=False, default=None)
    comments_expiry_date = DateTimeField(required=False, default=None)
    published = BooleanField(default=True)
    publish_date = DateTimeField(required=True, default=datetime.now)
    expiry_date = DateTimeField(required=False, default=None)
    link_url = StringField()

    meta = {
        'indexes': [('publish_date', 'slug'), '-publish_date', 'tags'],
    }

    _types = {}

    @queryset_manager
    def live_entries(queryset):
        cutoff_date = datetime.now().replace(hour=23, minute=59, second=59)
        queryset(Q(expiry_date__gt=datetime.now()) | Q(expiry_date=None),
                 published=True, publish_date__lte=cutoff_date)
        return queryset.order_by('-publish_date')

    @permalink
    def get_absolute_url(self):
        date = self.publish_date.strftime('%Y/%b/%d').lower()
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
        published = forms.BooleanField(required=False, initial=True)
        this_year = date.today().year
        publish_date = forms.DateTimeField(
            widget=SelectDateWidget(
                years=range(this_year-5, this_year+5)
            ),
        )
        publish_time = forms.TimeField()
        expiry_date = forms.DateTimeField(
            widget=SelectDateWidget(required=False),
            required=False)
        expiry_time = forms.TimeField(required=False)
        comments_enabled = forms.BooleanField(
            required=False,
            label="Comments",
            initial=True)
        choices = (
            ('never', 'Never'),
            ('week', '1 Week'),
            ('month', '1 Month'),
            ('half_year', '6 Monthes'),
        )
        comments_expiry = forms.ChoiceField(
            required=False, choices=choices)

        def clean(self):
            """Convert expiry options to actual dates and add publish time
            to publish date
            """
            data = self.cleaned_data

            if not self._errors:
                tags = data['tags']
                tags = tags.lower()
                if ',' in tags:
                    tags = [tag.strip() for tag in tags.split(',')]
                else:
                    tags = [tag.strip() for tag in tags.split()]
                data['tags'] = tags

                # We're using publish_time to get the time from the user - in
                # the DB its actually just part of publish_date, so update
                # publish_date to include publish_time's info
                publish_time = data['publish_time']
                expiry_time = data['expiry_time']
                if publish_time and data['publish_date']:
                    data['publish_date'] = data['publish_date'].replace(
                        hour=publish_time.hour,
                        minute=publish_time.minute,
                        second=publish_time.second)
                if expiry_time and data['expiry_date']:
                    data['expiry_date'] = data['expiry_date'].replace(
                        hour=expiry_time.hour,
                        minute=expiry_time.minute,
                        second=expiry_time.second)

                # The comments expiry date is selected and stored as a relative
                # time from the publish_date but it is useful to have an actual
                # expiry date too, so we work it out here
                comments_expiry = data['comments_expiry']
                publish_date = data['publish_date']
                if comments_expiry:
                    data['comments_expiry_date'] = {
                        # With no simple way of adding an exact month,
                        # approximate day representations are used
                        'never': lambda now: None,
                        'week': lambda now: now + timedelta(7),
                        'month': lambda now: now + timedelta(30),
                        'half_year': lambda now: now + timedelta(182),
                    }[comments_expiry](publish_date)
                else:
                    data['comments_expiry_date'] = None

            return data
        
    @classmethod
    def register(cls, entry_type):
        """Register an EntryType subclass.
        """
        cls._types[entry_type.type.lower()] = entry_type

import core
