import time

from django.conf import settings
from pymongo import MongoClient

client = MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
db = client[settings.MONGODB_NAME]
col = db.patent


def search_patent(fil, skip, limit=settings.ITEMS_PER_PAGE, ret_dict=True):
    time_search_start = time.time()

    cursor = col.find(fil, {'_id': False}).skip(skip).limit(limit)
    count = cursor.count()
    patents = []
    for document in cursor:
        patents.append(document['title'])

    time_search_end = time.time()
    search_time = time_search_end - time_search_start

    if ret_dict:
        return {
            'search_time': search_time,
            'count': count,
            'patents': patents
        }
    else:
        return patents