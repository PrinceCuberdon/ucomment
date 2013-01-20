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
"""
"Public" API
"""

import datetime

from ucomment.models import Comment, CommentPref

def post_message(message, url=None, message_url=None, ip=None):
    """ Post a message not a comment """
    if CommentPref.get_pref().use_notification:
        mess = Comment()
        mess.submission_date = datetime.datetime.now()
        mess.is_message = True
        if ip is not None:
            mess.ip = ip
        mess.content = message
        mess.url = '/'
        if message_url is not None:
            mess.message_url = message_url
        mess.visible = True
        mess.save()
