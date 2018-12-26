from django import template

from ..models import Rate, User

register = template.Library()


@register.filter
def to_int(value):
    return int(value)


@register.filter
def have_text_score(document):
    # try:
    #     return document._text_score
    # except Exception:
    #     return None
    try:
        return document['score']
    except Exception:
        return False


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, False)


@register.filter
def get(_list, index):
    try:
        return _list[index]
    except Exception:
        return None


@register.filter
def get_username(uid):
    return User.objects.get(id=uid).user_name


@register.filter
def x20(rate):
    return rate * 20


@register.filter
# 1000 -> 1,000
def number_with_commas(n):
    return '{:,}'.format(n)


@register.filter
def rate_times(patent):
    return len(Rate.objects.filter(patent_id=patent))


@register.filter
def get_progress_width(dictionary, star_point):
    return dictionary.get(star_point, 0)


@register.filter
def pop(dictionary: dict, v):
    clone = dictionary.copy()
    clone.pop(v, None)
    return clone


@register.filter
def build_query_string(queries_dictionary: dict):
    """Building query string from a dictionary of queries
        ex: {
            'search' : [2],
            'q': ['Hello world'],
            'sort': [3]
        }
        => search=2&q=Hello+World&sort=3
    """
    from urllib.parse import urlencode
    return urlencode(queries_dictionary, doseq=True)


@register.filter
def is_empty_query(query):
    return query == ['']


@register.filter
def word_trim(txt, n):
    """Trim text to (n) words"""
    return ' '.join(txt.split()[:n])


@register.filter
def add_int(s, v):
    return s + v


@register.filter
def minus_int(s, v):
    return s - v
