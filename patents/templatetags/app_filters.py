from django import template

from ..models import (
    User,
    Rate,
)

register = template.Library()


@register.filter
def to_int(value):
    return int(value)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, False)


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
    """
        Building query string from a dictionary of queries
        ex: {
            'search' : 2,
            'q': 'Hello world',
            'sort': 3
        }
        => search=2&q=Hello+World&sort=3
    """
    from urllib.parse import urlencode
    return urlencode(queries_dictionary, doseq=True)
