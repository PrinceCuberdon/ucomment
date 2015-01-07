# -*- coding: UTF-8 -*-
# ucomment is part of Band Cochon
# Band Cochon (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>

from django.contrib import admin

from .models import Comment, CommentPref, LikeDislike, CommentAbuse
#from core.common import TINYMCE_JS


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
        'get_abuse_count',
        'is_message',
    )
    
    list_editable = (
        'visible',
        'trash',
        'moderate',
    )
    
    list_filter = (
        'url',
        'submission_date',
        'user',
        'parent',
        'visible',
        'moderate',
        'is_message',
    )
    
    search_fields = (
        'url',
        'user__username',
        'content',
    )
    
    date_hierarchy = 'submission_date'

    #class Media:
    #    js = TINYMCE_JS


admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentPref)
admin.site.register(LikeDislike)
admin.site.register(CommentAbuse)