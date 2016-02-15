# -*- coding: UTF-8 -*-
# ucomment is part of Band Cochon
# Band Cochon (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>

from django import template
from django.conf import settings

import ucomment.API

register = template.Library()

START_SITE_MEDIA = len(settings.MEDIA_URL)


@register.filter
def comment_count(value):
    """ Get comment count for a picture """
    return ucomment.API.get_count(value)


@register.simple_tag
def get_total_comments_count(user):
    """ Get comments count for an user """
    return ucomment.API.get_count_for_user(user.id)

