from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django.contrib.syndication.feeds import Feed
from django.utils.feedgenerator import Atom1Feed
from django.core.exceptions import ObjectDoesNotExist

from datetime import datetime
from mongoengine.django.auth import REDIRECT_FIELD_NAME
from pymongo.son import SON

import entrytypes
from utils import csrf_protect
from entrytypes import markup

NO_ENTRIES_MESSAGES = (
    ('Have <a href="http://icanhazcheezburger.com">some kittens</a> instead.'),
    ('Have <a href="http://xkcd.com">a comic</a> instead.'),
    ('How about <a href="http://www.youtube.com/watch?v=oHg5SJYRHA0">'
     'a song</a> instead.'),
)

def archive(request, entry_type=None):
    """Display an archive of posts.
    """
    entry_types = [e.type for e in entrytypes.EntryType._types.values()]
    entry_class = entrytypes.EntryType
    type = "All"

    if entry_type and entry_type in [e.lower() for e in entry_types]:
        entry_class = entrytypes.EntryType._types[entry_type.lower()]
        type = entry_class.type

    entries = entry_class.live_entries().order_by('-date')[:10]

    context = {
        'title': 'Archive',
        'entry_types': entry_types,
        'entries': entries,
        'entry_type': type,
    }
    return render_to_response('mumblr/archive.html', context,
                              context_instance=RequestContext(request))

@login_required
def admin(request):
    """Display the main admin page.
    """
    entry_types = [e.type for e in entrytypes.EntryType._types.values()]
    entries = entrytypes.EntryType.objects.order_by('-date')[:10]

    context = {
        'title': 'Mumblr Admin',
        'entry_types': entry_types,
        'entries': entries,
        'datenow': datetime.now(),
    }
    return render_to_response('mumblr/admin.html', context,
                              context_instance=RequestContext(request))

@login_required
@csrf_protect('post')
def edit_entry(request, entry_id):
    """Edit an existing entry.
    """
    entry = entrytypes.EntryType.objects.with_id(entry_id)
    if not entry:
        return HttpResponseRedirect(reverse('admin'))

    # Select correct form for entry type
    form_class = entry.AdminForm

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            # Get necessary post data from the form
            for field, value in form.cleaned_data.items():
                entry[field] = value
            entry.tags = entry.tags.lower()
            if ',' in entry.tags:
                entry.tags = [tag.strip() for tag in entry.tags.split(',')]
            else:
                entry.tags = [tag.strip() for tag in entry.tags.split()]
            # Save the entry to the DB
            entry.save()
            return HttpResponseRedirect(reverse('recent-entries'))
    else:
        fields = entry._fields.keys()
        field_dict = dict([(name, entry[name]) for name in fields])
        # tags are stored as a list in the db, convert them back to a string
        field_dict['tags'] = ', '.join(field_dict['tags'])
        form = form_class(field_dict)

    context = {
        'title': 'Edit an entry',
        'type': type, 
        'form': form,
    }
    return render_to_response('mumblr/add_entry.html', context,
                              context_instance=RequestContext(request))

@login_required
@csrf_protect('post')
def add_entry(request, type):
    """Display the 'Add an entry' form when GET is used, and add an entry to
    the database when POST is used.
    """
    # 'type' must be a valid entry type (e.g. html, image, etc..)
    if type.lower() not in entrytypes.EntryType._types:
        raise Http404

    # Use correct entry type Document class
    entry_type = entrytypes.EntryType._types[type.lower()]
    # Select correct form for entry type
    form_class = entry_type.AdminForm

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            # Get necessary post data from the form
            entry = entry_type(**form.cleaned_data)
            entry.tags = entry.tags.lower()
            if ',' in entry.tags:
                entry.tags = [tag.strip() for tag in entry.tags.split(',')]
            else:
                entry.tags = [tag.strip() for tag in entry.tags.split()]
            # Save the entry to the DB
            entry.save()
            return HttpResponseRedirect(reverse('recent-entries'))
    else:
        form = form_class()

    context = {
        'title': 'Add %s Entry' % type,
        'type': type, 
        'form': form,
    }
    return render_to_response('mumblr/add_entry.html', context,
                              context_instance=RequestContext(request))

@login_required
@csrf_protect('get', 'post')
def delete_entry(request, entry_id):
    """Delete an entry from the database.
    """
    if entry_id:
        entrytypes.EntryType.objects.with_id(entry_id).delete()
    return HttpResponseRedirect(reverse('recent-entries'))

@login_required
@csrf_protect('get', 'post')
def delete_comment(request, comment_id):
    """Delete a comment from the database.
    """
    if comment_id:
        # Delete matching comment from entry
        entry = entrytypes.EntryType.objects(comments__id=comment_id).first()
        if entry:
            entry.comments = [c for c in entry.comments if c.id != comment_id]
            entry.save()
    return HttpResponseRedirect(entry.get_absolute_url()+'#comments')

def recent_entries(request, page_number=1):
    """Show the [n] most recent entries.
    """
    num = getattr(settings, 'MUMBLR_NUM_ENTRIES_PER_PAGE', 10)
    entry_list = entrytypes.EntryType.live_entries().order_by('-date')
    paginator = Paginator(entry_list, num)
    try:
        entries = paginator.page(page_number)
    except (EmptyPage, InvalidPage):
        entries = paginator.page(paginator.num_pages)
    context = {
        'title': 'Recent Entries',
        'entries': entries,
        'no_entries_messages': NO_ENTRIES_MESSAGES,
    }
    return render_to_response('mumblr/list_entries.html', context,
                              context_instance=RequestContext(request))

def entry_detail(request, date, slug):
    """Display one entry with the given slug and date.
    """
    try:
        date = datetime.strptime(date, "%Y/%b/%d")
    except:
        raise Http404

    try:
        entry = entrytypes.EntryType.objects(slug=slug).order_by('-date')[0]
    except IndexError:
        raise Http404

    # Select correct form for entry type
    form_class = entrytypes.Comment.CommentForm

    if request.method == 'POST':
        form = form_class(request.user, request.POST)
        if form.is_valid():
            # Get necessary post data from the form
            comment = entrytypes.core.HtmlComment(**form.cleaned_data)
            if request.user.is_authenticated():
                comment.is_admin = True
            # Update entry with comment
            q = entrytypes.EntryType.objects(id=entry.id)
            comment.rendered_content = markup(comment.body, True)
            q.update(push__comments=comment)

            return HttpResponseRedirect(entry.get_absolute_url()+'#comments')
    else:
        form = form_class(request.user)

    entry_url = entry.link_url or entry.get_absolute_url()
    context = {
        'title': '<a href="%s">%s</a>' % (entry_url, entry.title),
        'entry': entry,
        'datenow': datetime.now(),
        'form': form,
    }
    return render_to_response('mumblr/entry_detail.html', context,
                              context_instance=RequestContext(request))

def tagged_entries(request, tag=None, page_number=1):
    """Show a list of all entries with the given tag.
    """
    tag = tag.strip().lower()
    num = getattr(settings, 'MUMBLR_NUM_ENTRIES_PER_PAGE', 10)
    entry_list = entrytypes.EntryType.live_entries(tags=tag).order_by('-date')
    paginator = Paginator(entry_list, num)
    try:
        entries = paginator.page(page_number)
    except (EmptyPage, InvalidPage):
        entries = paginator.page(paginator.num_pages)
    context = {
        'title': 'Entries Tagged "%s"' % tag,
        'entries': entries,
        'no_entries_messages': NO_ENTRIES_MESSAGES,
    }
    return render_to_response('mumblr/list_entries.html', context,
                              context_instance=RequestContext(request))

def tag_cloud(request):
    """A page containing a 'tag-cloud' of the tags present on entries.
    """
    entries = entrytypes.EntryType.live_entries
    
    freqs = entries.item_frequencies('tags', normalize=True)
    freqs = sorted(freqs.iteritems(), key=lambda (k,v):(v,k))
    freqs.reverse()

    context = {
        'title': 'Tag Cloud',
        'tag_cloud': freqs,
    }
    return render_to_response('mumblr/tag_cloud.html', context,
                              context_instance=RequestContext(request))

class RssFeed(Feed):
    title = "Mumblr Recent Entries"
    link = "/"
    description = ""

    def items(self):
        return entrytypes.EntryType.live_entries.order_by('-date')[:30]

    def item_pubdate(self, item):
        return item.date

class AtomFeed(RssFeed):
    feed_type = Atom1Feed
    subtitle = RssFeed.description
