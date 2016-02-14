# -*- coding: UTF-8 -*-
# UComment - Django Universal Comment
# (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>

"""
Add call wrapper to decouple from the app
This prepare for an Micro Service
"""
from django.db.models import Q

__author__ = 'Prince Cuberdon'

from .models import Comment


def get_count(url='/', limit=-1):
    """
    Get the number of comments for an url

    :param url: The URL
    :type url: str
    :param limit: The limit of response
    :type limit: int
    :return: The number of comments for an url
    :rtype int
    """
    return len(get_comments(url, limit))


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
    comment_query = Q()
    for word in words:
        comment_query &= Q(content__icontains=word)

    return list(Comment.objects.filter(comment_query & Q(visible=True) & Q(trash=False) & Q(is_message=False)).order_by("submission_date"))
