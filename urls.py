# -*- coding: UTF-8 -*-
# ucomment is part of Band Cochon
# Band Cochon (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>
#
from django.conf.urls import url

import ucomment.views

urlpatterns = [
    url(
        r'^book/$',
        ucomment.views.BookView.as_view(),
        name="ucomment_book"
    ),

    url(r'^book/next/$',             ucomment.views.book_next),

    url(r'^ucomment/postmessage/$',  ucomment.views.postmessage,    name='ucomment_postmessage'),
    url(r'^ucomment/agree/$',        ucomment.views.agree,          name="ucomment_agree"),
    url(r'^ucomment/disagree/$',     ucomment.views.disagree,       name='ucomment_disagree'),
    url(r'^ucomment/moderate/$',     ucomment.views.moderate,       name='ucomment_moderate'),
    url(r'^ucomment/nextcomment/$',  ucomment.views.nextcomment,    name='ucomment_nextcomment'),
    url(r'^ucomment/showlast/$',     ucomment.views.showlast,       name='ucomment_showlast'),
    url(r'^ucomment/sendphoto/$',    ucomment.views.sendphoto,      name="ucomment_sendphoto"),
]
