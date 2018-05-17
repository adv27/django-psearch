from django import template

from ..models import User

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, False)


@register.filter
def get_username(uid):
    return User.objects.get(id=uid).user_name
