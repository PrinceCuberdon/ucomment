# -*- coding: UTF-8 -*-
# ucomment is part of Band Cochon
# Band Cochon (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>

from django import template
from django.db import connection
from django.conf import settings

from ucomment.models import Comment

register = template.Library()

START_SITE_MEDIA = len(settings.MEDIA_URL)

@register.filter
def comment_count(value):
    """ Get comment count for a picture """
    comments = Comment.objects.filter(visible=True)
    return comments.filter(url=value).only('id').count() + comments.filter(parent__url=value).only('id').count()

@register.simple_tag
def get_total_comments_count(user):
    """ Get comments count for an user """
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(id) FROM ucomment_comment WHERE user_id='%d'" % user.id)
    return cursor.fetchone()[0]


@register.filter
def ensure_site_media(value):
    """ Here for historical reason. Old avatar path are located with "avatar/IMAGE"
    not "/site_media/avatar/IMAGE" """
    if value[:START_SITE_MEDIA] != settings.MEDIA_URL:
        return settings.MEDIA_URL + value
    return value
