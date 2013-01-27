# -*- coding: UTF-8 -*-
# ucomment is part of Band Cochon
# Band Cochon (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('ucomment',
    url('^postmessage/$',   'views.postmessage',    name='ucomment_postmessage'),
    url(r'^agree/$',        'views.agree',          name="ucomment_agree"),
    url(r'^disagree/$',     'views.disagree',       name='ucomment_disagree'),
    url(r'^moderate/$',     'views.moderate',       name='ucomment_moderate'),
    url(r'^nextcomment/$',  'views.nextcomment',    name='ucomment_nextcomment'),
    url(r'^showlast/$',     'views.showlast',       name='ucomment_showlast'),
    url(r'^sendphoto/$',    'views.sendphoto',      name="ucomment_sendphoto"),
)