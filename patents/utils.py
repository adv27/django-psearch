from collections import Counter
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.files import File

from .models import *


def get_rate_percentage(rates):
    """
        Return percentage of each rating point (1->5) of 1 patent
    """
    c = Counter(list(map(lambda _r: _r.rating, rates)))
    rate_count = dict(c)
    rate_times = len(rates)
    for k, v in rate_count.items():
        rate_count[k] = v / rate_times * 100
    return rate_count


def create_user_validation(username, password):
    return len(User.objects.filter(user_name=username)) == 0


def create_user(username, password):
    user = User(
        user_name=username,
        password=password,
    )
    user.save()


def handle_uploaded_path(path):
    with open(path, 'rb') as f:
        django_f = File(f)
        f_name = os.path.basename(django_f.name)
        handle_uploaded_file(f_name, django_f.read())


def handle_uploaded_file(filename, filestream):
    import xmltodict
    import json

    _dict = xmltodict.parse(filestream)
    _json = json.dumps(_dict)
    doc = json.loads(_json)
    try:
        save_mongo(filename=filename, doc=doc)
        # if save_mongo is success
        # save the file uploaded to the MEDIA_ROOT
        cf = ContentFile(filestream)
        fs = FileSystemStorage()
        fs.save(name=filename, content=cf)
    except Exception as e:
        print('{} - Exception: {} - {}'.format(__name__, filename, e))


def handle_uploaded_file_unpack(args):
    handle_uploaded_file(*args)


def save_mongo(filename, doc):
    import pymongo
    from bson.json_util import loads
    try:
        # print(doc)

        title = doc['us-patent-application']['us-bibliographic-data-application']['invention-title']['#text']

        abstract = doc['us-patent-application']['abstract']

        if isinstance(abstract, list):
            abstract = get_values_recursive(abstract)
        else:
            abstract = abstract['p']['#text']

        detail = doc['us-patent-application']['description']['p']
        detail = '. '.join(list(map(lambda d: d['#text'], detail)))

        patent = Patent(
            filename=filename,
            title=title,
            abstract=abstract,
            content=detail,
        )
        patent = loads(patent.to_json())  # Document to JSON then to BSON
        '''
        Using pymongo client for multi processes purpose
        '''
        host = settings.MONGODB_HOST
        port = settings.MONGODB_PORT
        db = settings.MONGODB_NAME
        client = pymongo.MongoClient(host, port)[db]
        db = client.patent
        result = db.insert_one(patent)
        print(result.inserted_id)

    except Exception as e:
        raise e


def get_values_recursive(obj):
    if not isinstance(obj, str):
        t = ''
        for v in (obj.values() if isinstance(obj, dict) else obj):
            if v is None:
                continue
            p = get_values_recursive(v)
            if p is not None:
                t += p
        return t

    if not obj.isdigit() and len(obj) > 10:
        return obj + '\n'
    else:
        return None
