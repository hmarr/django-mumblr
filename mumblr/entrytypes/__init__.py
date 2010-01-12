from django import forms
from django.db.models import permalink
from django.forms.extras.widgets import SelectDateWidget

from datetime import datetime
import re
from uuid import uuid4
from mongoengine import *
from mongoengine.django.auth import User


class Comment(EmbeddedDocument):
    """A comment that may be embedded within a post.
    """
    id = StringField(required=True, default=uuid4)
    author = StringField()
    body = StringField()
    date = DateTimeField(required=True, default=datetime.now)

    def rendered_content(self):
        return self.body

    class CommentForm(forms.Form):

        author = forms.CharField()
        body = forms.CharField(widget=forms.Textarea)


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
    published = BooleanField(default=True)
    publish_date = DateTimeField(required=False, default=None)
    expiry_date = DateTimeField(required=False, default=None)
    link_url = StringField()

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

    @classmethod
    def register(cls, entry_type):
        """Register an EntryType subclass.
        """
        cls._types[entry_type.type.lower()] = entry_type
