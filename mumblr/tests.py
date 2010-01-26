from django.test import TestCase
from django.conf import settings

import mongoengine
from mongoengine.django.auth import User

import re
from datetime import datetime

from mumblr.entrytypes.core import TextEntry, HtmlComment, LinkEntry

mongoengine.connect('mumblr-unit-tests')


class MumblrTest(TestCase):

    urls = 'mumblr.urls'

    # Stop ORM-related stuff from happening as we don't use the ORM
    def _fixture_setup(self):
        pass
    def _fixture_teardown(self):
        pass

    def login(self):
        self.client.get('/admin/login/')
        data = self.user_data.copy()
        data['csrfmiddlewaretoken'] = self.get_csrf_token()
        return self.client.post('/admin/login/', data)

    def setUp(self):
        # Create a test user
        self.user_data = {
            'username': 'test',
            'password': 'testpassword123',
        }
        self.user = User.create_user(*self.user_data.values())

        # Create a test entry
        self.text_entry = TextEntry(title='Test-Entry', slug='test-entry')
        self.text_entry.tags = ['tests']
        self.text_entry.published = True
        self.text_entry.content = 'some-test-content'
        self.text_entry.rendered_content = '<p>some test content</p>'

        # Create test comment
        self.comment = HtmlComment(
            author='Mr Test',
            body='test comment',
            rendered_content = '<p>test comment</p>',
        )
        self.text_entry.comments = [self.comment]

        self.text_entry.save()

    def get_csrf_token(self):
        # Scrape CSRF token
        response = self.client.get('/admin/login/')
        csrf_regex = r'csrfmiddlewaretoken\'\s+value=\'(\w+)\''
        csrf_regex = r'value=\'(\w+)\''
        return re.search(csrf_regex, response.content).groups()[0]

    def test_recent_entries(self):
        """Ensure that the recent entries page works properly.
        """
        response = self.client.get('/')
        self.assertContains(response, self.text_entry.rendered_content, 
                            status_code=200)

    def test_entry_detail(self):
        """Ensure that the entry detail page works properly.
        """
        response = self.client.get(self.text_entry.get_absolute_url())
        self.assertContains(response, self.text_entry.rendered_content, 
                            status_code=200)

    def test_tagged_entries(self):
        """Ensure that the 'tagged entries' page works properly.
        """
        response = self.client.get('/tag/tests/')
        self.assertContains(response, self.text_entry.rendered_content, 
                            status_code=200)

        response = self.client.get('/tag/programming/')
        self.assertNotContains(response, self.text_entry.rendered_content, 
                               status_code=200)

    def test_tag_cloud(self):
        """Ensure that the 'tag cloud' page works properly.
        """
        response = self.client.get('/tags/')
        self.assertContains(response, 'tests', status_code=200)

    def test_add_link(self):
        """Ensure links get added properly, without nofollow attr
        """
        self.login()
        response = self.client.get('/admin/add/Lext')

        entry_data = {
            'title': 'Link Entry',
            'slug': 'link-entry',
            'tags': 'tests',
            'published': 'true',
            'content': 'test',
            'publish_date_year': datetime.now().year,
            'publish_date_month': datetime.now().month,
            'publish_date_day': datetime.now().day,
            'publish_time': datetime.now().strftime('%H:%M:%S'),
            'rendered_content': '<p>test</p>',
            'link_url': 'http://stevechallis.com/',
            'csrfmiddlewaretoken': self.get_csrf_token(),
        }
        # Check invalid form fails
        invalid_data = entry_data.copy()
        invalid_data['link_url'] = 'this-is-not-a-url'
        response = self.client.post('/admin/add/Link/', invalid_data)
        self.assertTemplateUsed(response, 'mumblr/admin/add_entry.html')

        # Check adding an entry does work
        response = self.client.post('/admin/add/text/', entry_data)
        entry = LinkEntry(slug=entry_data['slug'], publish_time=datetime.now())
        url = entry.get_absolute_url()
        self.assertRedirects(response, url, target_status_code=200)

        response = self.client.get(url)
        self.assertNotContains(response, 'rel="nofollow"')

        response = self.client.get('/')
        self.assertContains(response, entry_data['content'])

    def test_add_entry(self):
        """Ensure that entries may be added.
        """
        self.login()
        response = self.client.get('/admin/add/text/')

        entry_data = {
            'title': 'Second test entry',
            'slug': 'second-test-entry',
            'tags': 'tests',
            'published': 'true',
            'content': 'test',
            'publish_date_year': datetime.now().year,
            'publish_date_month': datetime.now().month,
            'publish_date_day': datetime.now().day,
            'publish_time': datetime.now().strftime('%H:%M:%S'),
            'rendered_content': '<p>test</p>',
            'csrfmiddlewaretoken': self.get_csrf_token(),
        }
        # Check invalid form fails
        response = self.client.post('/admin/add/text/', {
            'csrfmiddlewaretoken': self.get_csrf_token(),
            'content': 'test',
        })
        self.assertTemplateUsed(response, 'mumblr/admin/add_entry.html')

        # Check adding an entry does work
        response = self.client.post('/admin/add/text/', entry_data)
        entry = TextEntry(slug=entry_data['slug'], publish_time=datetime.now())
        url = entry.get_absolute_url()
        self.assertRedirects(response, url, target_status_code=200)

        response = self.client.get('/')
        self.assertContains(response, entry_data['content'])

    def test_add_comment(self):
        """Ensure that comments can be added
        """
        # Login to prevent Captcha
        self.login()
        add_url = self.text_entry.get_absolute_url()+'#comments'

        comment_data = {
            'author': 'Mr Test 2',
            'body': 'another-test-comment',
            'rendered_content': '<p>another-test-comment</p>',
            'csrfmiddlewaretoken': self.get_csrf_token(),
        }

        # Check invalid form fails
        response = self.client.post(add_url, {
            'body': 'test',
            'csrfmiddlewaretoken': self.get_csrf_token(),
        })

        # Check adding comment works
        response = self.client.post(add_url, comment_data)
        self.assertRedirects(response, add_url, target_status_code=200)

        response = self.client.get(add_url)
        self.assertContains(response, comment_data['rendered_content'])

    def test_edit_entry(self):
        """Ensure that entries may be edited.
        """
        self.login()
        edit_url = '/admin/edit/%s/' % self.text_entry.id

        entry_data = {
            'title': self.text_entry.title,
            'slug': self.text_entry.slug,
            'published': 'true',
            'publish_date_year': datetime.now().year,
            'publish_date_month': datetime.now().month,
            'publish_date_day': datetime.now().day,
            'publish_time': datetime.now().strftime('%H:%M:%S'),
            'content': 'modified-test-content',
            'csrfmiddlewaretoken': self.get_csrf_token(),
        }
        # Check invalid form fails
        response = self.client.post(edit_url, {
            'content': 'test',
            'csrfmiddlewaretoken': self.get_csrf_token(),
        })
        self.assertTemplateUsed(response, 'mumblr/admin/add_entry.html')

        # Check editing an entry does work
        response = self.client.post(edit_url, entry_data)
        entry = TextEntry(slug=entry_data['slug'], publish_time=datetime.now())
        url = entry.get_absolute_url()
        self.assertRedirects(response, url, target_status_code=200)

        response = self.client.get('/')
        self.assertContains(response, entry_data['content'])

    def test_delete_entry(self):
        """Ensure that entries may be deleted.
        """
        delete_url = '/admin/delete/'
        data = {
            'entry_id': self.text_entry.id,
            'csrfmiddlewaretoken': self.get_csrf_token(),
        }
        response = self.client.post(delete_url, data) 
        self.assertRedirects(response, '/admin/login/?next=' + delete_url,
                             target_status_code=200)

        self.login()

        data['csrfmiddlewaretoken'] = self.get_csrf_token()
        response = self.client.post(delete_url, data) 
        self.assertRedirects(response, '/')

        response = self.client.get('/')
        self.assertNotContains(response, self.text_entry.rendered_content, 
                               status_code=200)

    def test_delete_comment(self):
        """Ensure that comments can be deleted
        """
        self.login()

        data = {
            'comment_id': self.text_entry.comments[0].id,
            'csrfmiddlewaretoken': self.get_csrf_token(),
        }
        delete_url = '/admin/delete-comment/'

        response = self.client.post(delete_url, data)
        redirect_url = self.text_entry.get_absolute_url() + '#comments'
        self.assertRedirects(response, redirect_url)

        self.text_entry.reload()
        self.assertEqual(len(self.text_entry.comments), 0)

    def test_login_logout(self):
        """Ensure that users may log in and out.
        """
        # User not logged in
        response = self.client.get('/admin/login/')
        self.assertFalse(isinstance(response.context['user'], User))

        # User logging in
        data = self.user_data.copy()
        data['csrfmiddlewaretoken'] = self.get_csrf_token()
        response = self.client.post('/admin/login/', data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL, 
                             target_status_code=200)

        # User logged in
        response = self.client.get('/')
        self.assertTrue(isinstance(response.context['user'], User))

        response = self.client.get('/admin/logout/')
        self.assertRedirects(response, '/', target_status_code=200)

        # User logged out
        response = self.client.get('/admin/login/')
        self.assertFalse(isinstance(response.context['user'], User))

    def test_login_requred(self):
        """Ensure that a login is required for restricted pages.
        """
        restricted_pages = ['/admin/', '/admin/add/text/'] 
        restricted_pages.append('/admin/edit/%s/' % self.text_entry.id)
        restricted_pages.append('/admin/delete/')

        # Check in turn that each of the restricted pages may not be accessed
        for url in restricted_pages:
            response = self.client.get(url)
            self.assertRedirects(response, '/admin/login/?next=' + url,
                                 target_status_code=200)

        self.login()
        # Check in turn that each of the restricted pages may be accessed
        for url in restricted_pages:
            response = self.client.get(url, follow=True)
            self.assertFalse('/admin/login' in response.get('location', ''))

    def tearDown(self):
        self.user.delete()
        TextEntry.objects.delete()
