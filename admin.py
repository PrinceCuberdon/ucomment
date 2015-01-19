# -*- coding: UTF-8 -*-
# ucomment is part of Band Cochon
# Band Cochon (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>

from django.contrib import admin

from .models import Comment, CommentPref, LikeDislike, CommentAbuse
# from core.common import TINYMCE_JS


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        '__unicode__',
        'submission_date',
        'user',
        'external_user',
        'visible',
        'trash',
        'ip',
        'moderate',
        'abuse_count',
        'likeit',
        'dislikeit'
    )
    
    list_editable = (
        'visible',
        'trash',
        'abuse_count',
        'moderate',
        'likeit',
        'dislikeit'
    )
    
    list_filter = (
        'url',
        'submission_date',
        'user',
        'visible',
        'moderate'
    )
    
    search_fields = (
        'url',
        'user__username',
        'content',
    )
    
    date_hierarchy = 'submission_date'

    # class Media:
    #    js = TINYMCE_JS


class CommentPrefAdmin(admin.ModelAdmin):
    """
    Declaration for the Comment preferences
    """
    list_display = (
        '__unicode__',
        'only_registred',
        'use_like_dislike',
        'register_ip',
        'abuse_max'
    )
    
    list_editable = (
        'only_registred',
        'use_like_dislike',
        'register_ip',
        'abuse_max'        
    )


class LikeDislikeAdmin(admin.ModelAdmin):
    list_display = (
        '__unicode__',
        'user',
        'like',
        'dislike'
    )
    
admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentPref, CommentPrefAdmin)
admin.site.register(LikeDislike, LikeDislikeAdmin)
admin.site.register(CommentAbuse)