import getpass
import hashlib
from django.core.management.base import BaseCommand

from mongoengine.django.auth import User


class Command(BaseCommand):
    
    def _get_string(self, prompt, reader_func=raw_input, required=True):
        """Helper method to get a non-empty string.
        """
        string = ''
        while not string:
            string = reader_func(prompt + ': ')
            if not required:
                break
        return string

    def handle(self, **kwargs):
        username = self._get_string('Username')
        email = self._get_string('Email', required=False)
        password = self._get_string('Password', getpass.getpass)
        first_name = self._get_string('First name')
        last_name = self._get_string('Last name')

        user = User(username=username)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.set_password(password)
        user.is_staff = True
        user.save()

        print 'User "%s %s" successfully added' % (first_name, last_name)
