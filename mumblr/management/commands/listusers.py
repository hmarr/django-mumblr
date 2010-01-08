from django.core.management.base import BaseCommand

from mongoengine.django.auth import User


class Command(BaseCommand):

    def handle(self, **kwargs):
        for user in User.objects:
            print '[%s] %s' % (user.username, user.get_full_name())
