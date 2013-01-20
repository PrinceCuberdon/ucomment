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

from django.contrib import admin

from ucomment.models import Comment, CommentPref, LikeDislike, CommentAbuse

class CommentAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'submission_date', 'user', 'external_user', 'parent', 'visible', 'trash', 'ip', 'moderate', 'get_abuse_count','is_message',)
    list_editable = ('visible', 'trash',  'moderate', )
    list_filter = ('url', 'submission_date', 'user', 'parent', 'visible', 'moderate','is_message',)
    search_fields = ('url', 'user__username', 'content',)
    
    
admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentPref)
admin.site.register(LikeDislike)
admin.site.register(CommentAbuse)