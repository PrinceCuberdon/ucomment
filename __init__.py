# -*- coding: UTF-8 -*-
# ucomment is part of Band Cochon
# Band Cochon (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>

"""
Public API
"""

import datetime
from django.utils import timezone

from .models import Comment, CommentPref

def post_message(message, url=None, message_url=None, ip=None):
    """ Post a message not a comment """
    if CommentPref.get_pref().use_notification:
        mess = Comment()
        mess.submission_date = timezone.now()
        mess.is_message = True
        if ip is not None:
            mess.ip = ip
        mess.content = message
        mess.url = '/'
        if message_url is not None:
            mess.message_url = message_url
        mess.visible = True
        mess.save()
