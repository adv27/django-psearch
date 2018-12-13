from datetime import datetime

from mongoengine import *

# Create your models here.

class Patent(Document):
    filename = StringField(help_text='Name of XML file')
    created_at = DateTimeField(default=datetime.now())

    title = StringField(help_text='Title of Patent')
    abstract = StringField(help_text='Short description of Patent')
    content = StringField(help_text="Patent's content")
    rate = FloatField(help_text='Average rating', default=0)
    view = IntField(help_text='View times', default=0)

    meta = {
        'indexes': [
            {
                'fields': [
                    '$title',
                    '$abstract',
                    '$content',
                ], 'default_language': 'english',
            }
        ],
    }


class User(Document):
    user_name = StringField(help_text='Login name', required=True)
    password = StringField(help_text='password for login', required=True)
    query_first = DateTimeField(help_text='Date/time of first query')
    query_last = DateTimeField(help_text='Date/time of latest query')
    query_count = IntField(help_text='Query times', default=0)
    views = SortedListField(ReferenceField(Patent))

class Rate(Document):
    user_id = ReferenceField(User)
    patent_id = ReferenceField(Patent)
    rating = IntField(help_text="User's rate", min_value=1, max_value=5)
    date = DateTimeField(help_text='Date/time user make this rate')


class Search(Document):
    user_id = ReferenceField(User)
    keyword = StringField(help_text='Search keyword that user entered', null=True)
    date = DateTimeField(help_text='Date/time user make this search query')


class View(Document):
    search_id = ReferenceField(Search)
    patent_id = ReferenceField(Patent)
    date = DateTimeField(help_text='Date/time user view the patent')
