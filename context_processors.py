# -*- coding: UTF-8 -*-
# UComment - Django Universal Comment
# (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>

from .models import CommentPref


def ucomment(request):
    """ Put into the context, the page path """ 
    return {
        'PAGE_URI': request.META.get('PATH_INFO'),
        'ucomment_get_preferences': CommentPref.objects.get_preferences()
    }