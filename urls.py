# -*- coding: UTF-8 -*-
# UComment - Django Universal Comment
# (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>
#

from django.conf.urls import patterns, url

from .views import BookView

urlpatterns = patterns('',
    url(
        r'^book/$',
        BookView.as_view(),
        name="ucomment_book"
    ),

    url(r'^book/next/$', 'ucomment.views.book_next'),

    url(
        r'^ucomment/like/(\d+)/$',
        'ucomment.views.like_it',
        name='ucomment_like_it'
    ),

    url(
        r'^ucomment/dislike/(\d+)/$',
        'ucomment.views.dislike_it',
        name='ucomment_dislike_it'
    ),
    
    url(r'^ucomment/postmessage/$',  'ucomment.views.postmessage',    name='ucomment_postmessage'),
    url(r'^ucomment/moderate/$',     'ucomment.views.moderate',       name='ucomment_moderate'),
    url(r'^ucomment/nextcomment/$',  'ucomment.views.nextcomment',    name='ucomment_nextcomment'),
    url(r'^ucomment/showlast/$',     'ucomment.views.showlast',       name='ucomment_showlast'),
    url(r'^ucomment/sendphoto/$',    'ucomment.views.sendphoto',      name="ucomment_sendphoto"),
)
