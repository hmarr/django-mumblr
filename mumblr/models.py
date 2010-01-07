from mongoengine import *

from datetime import datetime


class User(Document):
    email = StringField(max_length=150, required=True)
    first_name = StringField(max_length=80)
    last_name = StringField(max_length=80)
    password = StringField(max_length=40)

import entrytypes.core
