# -*- coding: UTF-8 -*-
# UComment - Django Universal Comment
# (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>
#

from django.conf.urls import patterns, url

from .views import BookView

urlpatterns = patterns(
    '',

    url(
        r'^book/$',
        BookView.as_view(),
        name="ucomment_book"
    ),

    # url(r'^book/next/$', 'ucomment.views.book_next'),

    url(
        r'^ucomment/like/(\d+)/$',
        'ucomment.views.like_dislike',
        {'like': True, 'dislike': False},
        name='ucomment_like_it'
    ),

    url(
        r'^ucomment/dislike/(\d+)/$',
        'ucomment.views.like_dislike',
        {'like': False, 'dislike': True},
        name='ucomment_dislike_it'
    ),

    url(
        r'^ucomment/report/abuse/(?P<comment_id>\d+)/$',
        'ucomment.views.report_abuse',
        name='ucomment_report_abuse'
    ),

    url(
        r'^ucomment/add/$',
        'ucomment.views.add',
        name='ucomment_add_comment'
    ),

    #
    # url(r'^ucomment/postmessage/$',  'ucomment.views.postmessage',    name='ucomment_postmessage'),
    # url(r'^ucomment/moderate/$',     'ucomment.views.moderate',       name='ucomment_moderate'),
    # url(r'^ucomment/nextcomment/$',  'ucomment.views.nextcomment',    name='ucomment_nextcomment'),
    # url(r'^ucomment/showlast/$',     'ucomment.views.showlast',       name='ucomment_showlast'),

    url(
        r'^ucomment/send_files/$',
        'ucomment.views.send_files',
        name="ucomment_send_files"
    ),
)
