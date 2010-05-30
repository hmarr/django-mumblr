from django.template import Library, Node, TemplateSyntaxError

import re

from mumblr.entrytypes import EntryType

register = Library()


class LatestEntriesNode(Node):

    def __init__(self, num, var_name):
        self.num = int(num or 10)
        self.var_name = var_name

    def render(self, context):
        context[self.var_name] = list(EntryType.live_entries()[:self.num])
        return ''


@register.tag
def get_latest_entries(parser, token):
    # Usage:
    #   {% get_latest_entries as entries %} (default 10 entries)
    #   (or {% get_latest_entries 7 as entries %} for 7 entries)
    #   {% for entry in entries %}
    #       <li>{{ entry.title }}</li>
    #   {% endfor %}
    tag_name, contents = token.contents.split(None, 1)
    match = re.search(r'(\d+\s+)?as\s+([A-z_][A-z0-9_]+)', contents)
    if not match:
        raise TemplateSyntaxError("%r tag syntax error" % tag_name)

    num, var_name = match.groups()
    return LatestEntriesNode(num, var_name)
