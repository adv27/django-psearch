from datetime import datetime

from django.db import models
from mongoengine import *


# Create your models here.

class Patent(Document):
    filename = StringField(help_text='Name of XML file')
    created_at = DateTimeField(default=datetime.utcnow)

    title = StringField(help_text='Title of Patent')
    abstract = StringField(help_text='Short description of Patent')
    content = StringField(help_text="Patent's content")

    meta = {'indexes': [
        {
            'fields': [
                '$title',
                '$abstract',
                "$content"
            ], 'default_language': 'english',
        }
    ]}


class User():
    pass


class Rate(models.Model):
    pass


class Search(models.Model):
    pass


class View(models.Model):
    pass
