import os
from multiprocessing import Pool
from os.path import exists, join, splitext

from django.conf import settings
from pymongo import MongoClient

from .models import Patent
from .utils import chunks, get_file_content, xml2patent, handle_file_path


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

    'if the file name already in the db, then skip it'
    f_in = Patent.objects(filename__in=file_names)
    f_in = list(map(lambda d: d['filename'], f_in))
    f_in = []
    file_names = set(file_names) - set(f_in)

    'join the file name with the directory path, to get the file path on computer'
    file_paths = list(map(lambda f_name: join(path, f_name), file_names))

    processes = settings.BULK_INSERT_PROCESSES

    paths2chunks = chunks(file_paths, processes)

    with Pool(processes=processes) as pool:
        pool.map(bulk, paths2chunks)
        pool.close()
        pool.join()


def bulk(paths):
    """Using pymongo's insert_many to bulk insert."""
    from bson import json_util

    # read contents from all paths, then convert content to patent, then bson
    contents_and_names = list(map(lambda path: handle_file_path(path), paths))
    patents = map(lambda c: xml2patent(c['content']), contents_and_names)
    patents_bson = map(lambda p: json_util.loads(p), patents)

    # connect to mongodb
    host = settings.MONGODB_HOST
    port = settings.MONGODB_PORT
    db = settings.MONGODB_NAME
    client = MongoClient(host, port)[db]
    db = client.patent

    result = db.insert_many(patents_bson)
    # print(result.inserted_id)
