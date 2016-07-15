# -*- coding: UTF-8 -*-
# UComment - Django Universal Comment
# (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>

"""
Add call wrapper to decouple from the app
This prepare for an Micro Service
"""
from django.db.models import Q

from .models import Comment

__author__ = 'Prince Cuberdon'


def get_count(url='/'):
    """
    Get the number of comments for an url

    :param url: The URL
    :type url: str
    :param limit: The limit of response
    :type limit: int
    :return: The number of comments for an url
    :rtype int
    """
    return len(get_comments(url))


def get_comments(url='/', limit=-1):
    """
    Get all comments for URL
    :param url: The url
    :type url: str
    :param limit: The limit of response
    :type limit: int
    :return:
    :rtype list
    """
    return Comment.objects.get_for_url(url, limit)


def search_words(words):
    """
    Search a list of words inside commentaries
    :param words:  A words list
    :type words: list
    :return: A list of comment
    :rtype list
    """
    comment_query = Q(visible=True, trash=False, is_message=False)

    for word in words:
        comment_query &= Q(content__icontains=word)

    return list(Comment.objects.filter(comment_query).order_by("submission_date"))


def get_count_for_user(id):
    """
    Get count for an user.
    :param id: The user id
    :type id: int
    :return: The number of visible message
    :rtype: int
    """
    return Comment.objects.filter(user__pk=id, trash=False, visible=True, is_message=True).only('id').count()


def post_comment(user, url, message, raw_html=False):
    """
    Post a message on the wall

    :param raw_html: Is the message is in raw HTML
    :type raw_html: bool
    :param user: The user that post the messavge
    :type user: django.contrib.auth.models.User
    :param url: The message title
    :type url: str
    :param message: The message by itself
    :type message: unicode
    :return: The comment inserted object
    :rtype: ucomment.models.Comment
    """
    return Comment.objects.post_comment(url=url, message=message, user=user, parent=None, raw_html=raw_html)
