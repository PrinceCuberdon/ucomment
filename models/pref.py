# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _

class CommentPrefManager(models.Manager):
    """
    Manager for the comment preferences
    """
    def get_preferences(self):
        """ Return preferences for Comment. Create with default values if not exists """
        prefs = self.get_queryset().all()
        return CommentPref.objects.create() if prefs.count() == 0 else list(prefs)[-1]


class CommentPref(models.Model):
    """ Preferences for UComment """
    only_registred = models.BooleanField(
        default=True,
        verbose_name=_("Only registered"),
        help_text=_("Only registered user can post (if no, every body can post)")
    )

    use_like_dislike = models.BooleanField(
        default=True,
        verbose_name=_("Use Like Dislike"),
        help_text=_("Use the like and dislike system.")
    )

    register_ip = models.BooleanField(
        default=True,
        verbose_name=_("Register IP"),
        help_text=_("Save IP address on each post")
    )

    abuse_max = models.SmallIntegerField(
        default=3,
        verbose_name=_("Maximum abuse"),
        help_text=_("Maximum abuse count before moderation")
    )

    objects = CommentPrefManager()

    def __unicode__(self):
        return "Comment Preferences : #%d" % self.pk

    class Meta:
        app_label = "ucomment"
        verbose_name = _("Preference")
        verbose_name_plural = _("Preferences")