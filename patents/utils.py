import json
import os
from collections import Counter

from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

from .models import *


def handle_file_path(path):
    """Read file's content by path
    Return a dictionary contains file name and it's content.
    """
    with open(path, 'rb') as f:
        django_f = File(f)
        f_name = os.path.basename(django_f.name)
        return {
            'name': f_name,
            'content': django_f.read()
        }


def xml2json(xml):
    import xmltodict

    _dict = xmltodict.parse(xml)
    _json = json.dumps(_dict)
    return json.loads(_json)


def get_file_content(path):
    with open(path, 'rb') as f:
        return f.read()


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_rate_percentage(rates):
    """Return percentage of each rating point (1->5) of 1 patent."""
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


def read_file(path):
    """Read file by path then return file content.

    :param path: path of file to read
    :return: file content
    """
    with open(path, 'rb') as f:
        django_f = File(f)
        return django_f.read()


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
        '''Using pymongo client for multi processes purpose.'''
        host = settings.MONGODB_HOST
        port = settings.MONGODB_PORT
        db = settings.MONGODB_NAME
        client = pymongo.MongoClient(host, port)[db]
        db = client.patent
        result = db.insert_one(patent)
        print(result.inserted_id)

    except Exception as e:
        raise e


def get_paginate(page_no, num_pages):
    """We assume that if there are more than 11 pages
    (current, 5 before, 5 after) we are always going to show 11 links.
    Now we have 4 cases:
        Number of pages < 11: show all pages;
        Current page <= 6: show first 11 pages;
        Current page > 6 and < (number of pages - 6): show current page, 5 before and 5 after;
        Current page >= (number of pages -6): show the last 11 pages.
    """
    if num_pages <= 11 or page_no <= 6:  # case 1 and 2
        return list(range(1, min(num_pages + 1, 12)))
    elif page_no > num_pages - 6:  # case 4
        return list(range(num_pages - 10, num_pages + 1))
    else:  # case 3
        return list(range(page_no - 5, page_no + 6))


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


def parse_xml(filestream, filename):
    doc = xml2json(filestream)

    if 'us-patent-application' in doc:
        # type 1
        # print('{} - type 1'.format(filename))
        title = doc['us-patent-application']['us-bibliographic-data-application']['invention-title']['#text']

        abstract = doc['us-patent-application']['abstract']

        if isinstance(abstract, list):
            abstract = get_values_recursive(abstract)
        else:
            abstract_p = abstract['p']
            if isinstance(abstract_p, list):
                abstract_p_have_text =  filter(lambda ap: '#text' in ap, abstract_p)
                abstract = '. '.join((map(lambda apht: apht['#text'], abstract_p_have_text)))
            elif isinstance(abstract_p, dict) and '#text' in abstract_p:
                abstract = abstract['p']['#text']

        detail = doc['us-patent-application']['description']['p']
        detail_have_text = filter(lambda de: '#text' in de, detail)
        detail = '. '.join((map(lambda d: d['#text'], detail_have_text)))
    elif 'patent-application-publication' in doc:
        # type 2
        # print('{} - type 2'.format(filename))
        title = doc['patent-application-publication'] \
            ['subdoc-bibliographic-information'] \
            ['technical-information'] \
            ['title-of-invention']

        abstract = doc['patent-application-publication']['subdoc-abstract']['paragraph']

        detail = doc['patent-application-publication'] \
            ['subdoc-description'] \
            ['detailed-description'] \
            ['section']

        if 'paragraph' in detail:
            para_have_text = filter(lambda pp: '#text' in pp, detail['paragraph'])
            para = '. '.join(map(lambda pr: pr['#text'], para_have_text))
            detail = para
        else:
            para = []
            for s in detail:
                if 'paragraph' in s:
                    ppp = s['paragraph']
                    if isinstance(ppp, list):
                        for p in ppp:
                            if '#text' in p:
                                para.append(p['#text'])
                    elif isinstance(ppp, dict) and '#text' in ppp:
                        para.append(ppp['#text'])
            detail = '. '.join(para)
    else:
        raise Exception('Not supported type - {}'.format(filename))

    return {
        'title': title,
        'abstract': abstract,
        'content': detail
    }


def test_parse_xml(path):
    with open(path, 'rb') as f:
        django_f = File(f)
        f_name = os.path.basename(django_f.name)
        return parse_xml(f.read(), f_name)
