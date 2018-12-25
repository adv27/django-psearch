import time

from django.conf import settings
from pymongo import MongoClient

client = MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
db = client[settings.MONGODB_NAME]
col = db.patent


def search_patent(fil, skip, limit=settings.ITEMS_PER_PAGE, string_id=True, time_search=False):
    time_search_start = time.time()

    cursor = col.find(fil).skip(skip).limit(limit)
    count = cursor.count()
    patents = []
    for document in cursor:
        if string_id:
            str_id = str(document['_id'])
            del(document['_id'])
            document['id'] = str_id
        patents.append(document)

    time_search_end = time.time()
    search_time = time_search_end - time_search_start

    if time_search:
        return patents, count, search_time
    return patents, count