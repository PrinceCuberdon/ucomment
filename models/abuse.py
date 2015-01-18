# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User


class CommentAbuse(models.Model):
    """
    Comment abuse declaration. An user can only signal one post as an abuse
    """
    user = models.ForeignKey(User)
    comment = models.ForeignKey('Comment')

    class Meta:
        app_label = "ucomment"
