from django.test import TestCase
from django.conf import settings

import mongoengine
from mongoengine.django.auth import User

from mumblr.entrytypes.core import HtmlEntry

mongoengine.connect('mumblr-unit-tests')


class MumblrTest(TestCase):

    urls = 'mumblr.urls'

    # Stop ORM-related stuff from happening as we don't use the ORM
    def _fixture_setup(self):
        pass

    def login(self):
        return self.client.post('/admin/login/', self.user_data)

    def setUp(self):
        # Create a test user
        self.user_data = {
            'username': 'test',
            'password': 'testpassword123',
        }
        self.user = User.create_user(*self.user_data.values())

        # Create a test entry
        self.html_entry = HtmlEntry(title='Test Entry', slug='test-entry')
        self.html_entry.tags = ['tests']
        self.html_entry.published = True
        self.html_entry.content = 'some test content'
        self.html_entry.rendered_content = '<p>some test content</p>'
        self.html_entry.save()

    def test_recent_entries(self):
        """Ensure that the recent entries page works properly.
        """
        response = self.client.get('/')
        self.assertContains(response, self.html_entry.rendered_content, 
                            status_code=200)

    def test_entry_detail(self):
        """Ensure that the recent entries page works properly.
        """
        response = self.client.get(self.html_entry.get_absolute_url())
        self.assertContains(response, self.html_entry.rendered_content, 
                            status_code=200)

    def test_tagged_entries(self):
        """Ensure that the 'tagged entries' page works properly.
        """
        response = self.client.get('/tag/tests/')
        self.assertContains(response, self.html_entry.rendered_content, 
                            status_code=200)

        response = self.client.get('/tag/programming/')
        self.assertNotContains(response, self.html_entry.rendered_content, 
                               status_code=200)

    def test_tag_cloud(self):
        """Ensure that the 'tag cloud' page works properly.
        """
        response = self.client.get('/tags/')
        self.assertContains(response, 'tests', status_code=200)

    def test_add_entry(self):
        """Ensure that entries may be added.
        """
        self.login()
        response = self.client.get('/admin/add/html/')
        csrf_token = response.context['csrf_token']

        entry_data = {
            'title': 'Second test entry',
            'slug': 'second-test-entry',
            'tags': 'tests',
            'published': 'true',
            'content': '<p>test</p>',
        }
        # Check CSRF-proof
        response = self.client.post('/admin/add/html/', entry_data)
        self.assertEqual(response.status_code, 403)

        # Check invalid form fails
        response = self.client.post('/admin/add/html/', {
            settings.CSRF_COOKIE_NAME: csrf_token,
            'content': 'test',
        })
        self.assertTemplateUsed(response, 'mumblr/add_entry.html')

        # Check adding an entry does work
        entry_data[settings.CSRF_COOKIE_NAME] = csrf_token
        response = self.client.post('/admin/add/html/', entry_data)
        self.assertRedirects(response, '/', target_status_code=200)

        response = self.client.get('/')
        self.assertContains(response, entry_data['content'])

    def test_edit_entry(self):
        """Ensure that entries may be edited.
        """
        self.login()
        edit_url = '/admin/edit/%s/' % self.html_entry.id
        response = self.client.get(edit_url)
        csrf_token = response.context['csrf_token']

        entry_data = {
            'title': self.html_entry.title,
            'slug': self.html_entry.slug,
            'published': 'true',
            'content': 'modified test content',
        }
        # Check CSRF-proof
        response = self.client.post(edit_url, entry_data)
        self.assertEqual(response.status_code, 403)

        # Check invalid form fails
        response = self.client.post(edit_url, {
            settings.CSRF_COOKIE_NAME: csrf_token,
            'content': 'test',
        })
        self.assertTemplateUsed(response, 'mumblr/add_entry.html')

        # Check editing an entry does work
        entry_data[settings.CSRF_COOKIE_NAME] = csrf_token
        response = self.client.post(edit_url, entry_data)
        self.assertRedirects(response, '/', target_status_code=200)

        response = self.client.get('/')
        self.assertContains(response, entry_data['content'])

    def test_delete_entry(self):
        """Ensure that entries may be deleted.
        """
        self.login()
        response = self.client.get('/')
        csrf_token = response.context['csrf_token']

        delete_url = '/admin/delete/%s/' % self.html_entry.id
        # Check CSRF-proof
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 403)

        token_name = settings.CSRF_COOKIE_NAME
        response = self.client.get(delete_url + '?%s=%s' % 
                                   (settings.CSRF_COOKIE_NAME, csrf_token))
        self.assertRedirects(response, '/')

        response = self.client.get('/')
        self.assertNotContains(response, self.html_entry.rendered_content, 
                               status_code=200)

    def test_login_logout(self):
        """Ensure that users may log in and out.
        """
        # User not logged in
        response = self.client.get('/admin/login/')
        self.assertFalse(isinstance(response.context['user'], User))

        # User logging in
        response = self.client.post('/admin/login/', self.user_data)
        self.assertRedirects(response, '/', target_status_code=200)

        # User logged in
        response = self.client.get('/')
        self.assertTrue(isinstance(response.context['user'], User))

        csrf_token = response.context['csrf_token']

        # Check that log out is CSRF-proof
        response = self.client.get('/admin/logout/')
        self.assertEqual(response.status_code, 403)

        response = self.client.get('/admin/logout/?%s=%s' % 
                                   (settings.CSRF_COOKIE_NAME, csrf_token))
        self.assertRedirects(response, '/admin/login/', target_status_code=200)

        # User logged out
        response = self.client.get('/admin/login/')
        self.assertFalse(isinstance(response.context['user'], User))

    def test_login_requred(self):
        """Ensure that a login is required for restricted pages.
        """
        restricted_pages = ['/admin/', '/admin/add/html/'] 
        restricted_pages.append('/admin/edit/%s/' % self.html_entry.id)
        restricted_pages.append('/admin/delete/%s/' % self.html_entry.id)

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
        HtmlEntry.objects.delete()
