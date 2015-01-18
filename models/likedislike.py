# -*- coding: UTF-8 -*-
# UComment - Django Universal Comment
# (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>
#

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.db import models
from django.contrib.auth.models import User


class LikeDislike(models.Model):
    """
    Save if an user has yet voted for a comment
    """
    comment = models.ForeignKey(
        "Comment"
    )

    like = models.BooleanField(
        default=False,
        db_index=True
    )

    dislike = models.BooleanField(
        default=False,
        db_index=True
    )

    user = models.ForeignKey(
        User,
        db_index=True,
        null=True,
        blank=True,
        related_name="ld_user"
    )

    def __unicode__(self):
        return self.comment.url

    class Meta:
        app_label = "ucomment"


@receiver(post_save, sender=LikeDislike)
def increase_like_dislike(sender, **kwargs):
    """
    When a LikeDislike entry is created, the related comment entry
    is updated.
    """
    comment = kwargs['instance'].comment
    if kwargs['instance'].like:
        comment.likeit += 1

    elif kwargs['instance'].dislike:
        comment.dislikeit += 1

    comment.save()

