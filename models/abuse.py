# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class CommentAbuse(models.Model):
    """
    Comment abuse declaration. An user can only signal one post as an abuse
    """
    user = models.ForeignKey(User)
    comment = models.ForeignKey('Comment')

    def __unicode__(self):
        return self.user.get_username()

    class Meta:
        app_label = "ucomment"
        verbose_name = _("Abuse reported")
        verbose_name_plural = _("Abuses reported")
