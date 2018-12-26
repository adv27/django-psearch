import os
import time
import traceback
from os.path import basename, exists, join, splitext

from bson import json_util
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from pymongo import MongoClient

from .models import Patent
from .utils import chunks, handle_file_path, parse_xml, read_file, xml2json

from multiprocessing import Pool

def get_db():
    # connect to mongodb
    host = settings.MONGODB_HOST
    port = settings.MONGODB_PORT
    client = MongoClient(host, port)
    db = client[settings.MONGODB_NAME]
    return db

def read_and_parse_xml_wrapper(p):
    # read file
    file_content = read_file(p)
    filename = basename(p)

    # parse xml content
    try:
        parsed_xml = parse_xml(filestream=file_content, filename=filename)
    except Exception as e:
        print('{} - {}'.format(e, filename))
        print(traceback.format_exc())
        parsed_xml = None

    fc_mapping = {
        'path': p,
        'filename': filename,
        'content': file_content,
        'parse': parsed_xml
    }

    return fc_mapping

def insert(path):
    path_exist = exists(path)
    if not path_exist:
        print('Path not exits!')
        return

    'get all file names in path'
    file_names = os.listdir(path)

    'filter the file name list, only take .xml file'
    file_names = list(filter(lambda f_name: splitext(f_name.lower())[1] == '.xml', file_names))

    print('There are {} XML files in {}'.format(len(file_names), path))

    item_per_insert = settings.BULK_INSERT_PER

    filenames2chunks = chunks(file_names, item_per_insert)

    db = get_db()

    for f_names in filenames2chunks:
        'if the file name already in the db, then skip it'
        f_in = Patent.objects(filename__in=f_names)
        f_in = list(map(lambda d: d['filename'], f_in))
        f_in = []
        f_names_filter = set(f_names) - set(f_in)

        'join the file name with the directory path, to get the file path on computer'
        paths = list(map(lambda f_name: join(path, f_name), f_names_filter))

        print('Start parse {} file(s)'.format(len(paths)))

        # read file contents & parse xml content
        time_parse_start = time.time()
        file_contents_mapping = []

        # using multi processing for better performance
        with Pool(processes=settings.BULK_INSERT_PROCESSES) as pool:
            file_contents_mapping = pool.map(read_and_parse_xml_wrapper, paths)
            pool.close()
            pool.join()

        # filter un parsed xml
        tmp = filter(lambda x: x['parse'] is not None, file_contents_mapping)
        file_contents_mapping = list(tmp)
        time_parse_end = time.time()
        time_parse = time_parse_end - time_parse_start
        print('Parsed {} file(s) in {}'.format(len(file_contents_mapping), time_parse))

        # make list of json querydetail = '. '.join(list(map(lambda d: d['#text'], detail)))
        patents = map(lambda f: Patent(f['filename'], **f['parse']), file_contents_mapping)
        patents_json = map(lambda pat: json_util.loads(pat.to_json()), patents)

        # bulk insert
        if file_contents_mapping:
            time_insert_start = time.time()
            in_ids = db.test.insert_many(patents_json).inserted_ids
            time_insert_end = time.time()
            time_insert = time_insert_end - time_insert_start
            print('Inserted {} in time {}'.format(len(in_ids), time_insert))
        else:
            print('No operations to execute')

        print('-' * 50)

        # if save_mongo is success
        # save the file uploaded to the MEDIA_ROOT
        if settings.BULK_INSERT_SAVE_FILE:
            fs = FileSystemStorage()
            for fcm in file_contents_mapping:
                cf = ContentFile(fcm['content'])
                filename = basename(fcm['path'])
                fs.save(name=filename, content=cf)


def bulk(paths):
    """Using pymongo's insert_many to bulk insert."""
    from bson import json_util

    # read contents from all paths, then convert content to patent, then bson
    contents_and_names = list(map(lambda path: handle_file_path(path), paths))
    patents = map(lambda c: xml2json(c['content']), contents_and_names)
    patents_bson = map(lambda p: json_util.loads(p), patents)

    # connect to mongodb
    host = settings.MONGODB_HOST
    port = settings.MONGODB_PORT
    client = MongoClient(host, port)
    db = client[settings.MONGODB_NAME]
    col = db.patent

    result = col.insert_many(patents_bson)
    # print(result.inserted_id)
