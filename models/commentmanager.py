# -*- coding: utf-8 -*-
# UComment - Django Universal Comment
# (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>
#

from django.db import models


class CommentManager(models.Manager):
    """
    Define a manager for Comment model
    """
    def get_for_url(self, url, count=-1):
        """
        Get last comments for the url
        """
        if count == -1:
            # Get all
            comments = list(self.get_queryset().filter(
                visible=True,
                trash=False,
                url=url,
                parent=None
            ))
        else:
            comments = list(self.get_queryset().filter(
                visible=True,
                trash=False,
                url=url,
                parent=None
            )[:count])

        # Get and regroup sons
        comments_son = {}
        result = list(self.get_queryset().filter(
            parent__in=[comment.pk for comment in comments]
            ).order_by('submission_date'))

        for son in result:
            if son.parent.pk not in comments_son:
                comments_son[son.parent.pk] = []
            comments_son[son.parent.pk].append(son)

        # Attribute sons to parents
        for com in comments:
            if com.pk in comments_son:
                com.get_response = comments_son[com.pk]
            else:
                com.get_response = None
            
        return comments
    
    def get_count_for_url(self, url):
        """
        Get how many comments there is for a particular url
        """
        comments = list(self.get_queryset().filter(
            visible=True,
            trash=False,
            url=url,
            parent=None
            ))
        ids = [comment.pk for comment in comments]
        sub_comments = list(self.get_queryset().filter(parent__in=ids))
        return len(comments) + len(sub_comments)
