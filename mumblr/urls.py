from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout

from views import (recent_entries, tagged_entries, delete_entry, add_entry, 
                   edit_entry, entry_detail, admin, log_in, tag_cloud, log_out)

urlpatterns = patterns('',
    url('^$', recent_entries, name='recent-entries'),
    url('^(?P<page_number>\d+)/$', recent_entries, name='recent-entries'),
    url('^(\d{4}/\w{3}/\d{2})/([\w-]+)/$', entry_detail, name='entry-detail'),
    url('^tag/(?P<tag>[a-z0-9_-]+)/$', tagged_entries, name='tagged-entries'),
    url('^tag/(?P<tag>[a-z0-9_-]+)/(?P<page_number>\d+)/$', tagged_entries, 
        name='tagged-entries'),
    url('^tags/$', tag_cloud, name='tag_cloud'),
    url('^admin/$', admin, name='admin'),
    url('^admin/add/(\w+)/$', add_entry, name='add-entry'),
    url('^admin/edit/(\w+)/$', edit_entry, name='edit-entry'),
    url('^admin/delete/(\w+)/$', delete_entry, name='delete-entry'),
    url('^admin/login/$', login, {'template_name': 'mumblr/log_in.html'}, 
        name='log-in'),
    url('^admin/logout/$', logout, {'next_page': '/'}, name='log-out'),
)
