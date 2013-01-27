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


import re
import shutil
import os

from django.db import models
from django.contrib.auth.models import User as AuthUser
from django.template.defaultfilters import linebreaksbr, striptags
from django.conf import settings

import memcache

# Only on client instance  
_client = memcache.Client((settings.CACHES['default']['LOCATION'],))

from common import convert_date

class CommentPrefManager(models.Manager):
    def get_pref(self):
        """ Return preferences for Comment. Create with default values if not exists """
        try:
            return CommentPref.objects.lastest('id')
        except:
            pass
        
        return CommentPref.objects.create()
    
class CommentPref(models.Model):
    """ Preferences for UComment """
    only_registred = models.BooleanField(default=True)
    use_like_dislike = models.BooleanField(default=True)
    publish_on_submit = models.BooleanField(default=True)
    register_ip = models.BooleanField(default=True)
    abuse_max = models.SmallIntegerField(default=3, verbose_name="Abus maximum", help_text=u"Nombre d'abus maximum avant que le message ne passe en modération")
    use_notification = models.BooleanField(default=False, verbose_name="Notification", help_text=u"Use notification inside the Wall")
    
    objects = CommentPrefManager()

    @classmethod
    def get_pref(self):
        """ Singleton : get preferences """
        try:
            return CommentPref.objects.lastest('id')
        except:
            pass
        
        return CommentPref.objects.create()

    def __unicode__(self):
        return "Comment Preferences : #%d" % self.pk
       
class CommentAbuse(models.Model):
    user = models.ForeignKey(AuthUser)
    comment = models.ForeignKey('Comment')
    
    
class LikeDislike(models.Model):
    comment = models.ForeignKey("Comment")
    like = models.BooleanField(default=False, db_index=True)
    dislike = models.BooleanField(default=False, db_index=True)
    user = models.ForeignKey(AuthUser, db_index=True, null=True, blank=True, related_name="ld_user")

    def __unicode__(self):
        return self.comment.url
    
NEW_YOUTUBE_CODE = '''<iframe width="560" height="315" src="http://www.youtube.com/embed/\\1" frameborder="0" allowfullscreen></iframe>'''
NEW_DAILYMOTION_CODE = '''<iframe frameborder="0" width="560" height="315" src="http://www.dailymotion.com/embed/video/\\1"></iframe><br>'''

SMILEYS = (
    (r'O:\)|O:-\)',                 'angel'),
    (r':p|:-p',                     'raspberry'),
    (r';\)|;-\)',                   'wink'),
    ##(r'\^8\^',                    'bat'),
    (r'\>:\)|\>:-\)|\]:-\)|\]:\)',  'devilish'),
    (r'8\||8-\||B\)|B-\)',          'cool'),
    (r":'\(|:'-\(",                 'crying'),
    (r':\$',                         'embarrassed'),
    (r'8\)|8-\)',                   'glasses'),
    (r':\*|:-\*',                   'kiss'),
    (r':D|:-D',                     'laugh'),
    (r':\||:-\|',                   'uncertain'),
    (r':\(|:-\(',                   'sad'),
    (r'\+o\(',                      'sick'),
    (r':o|:O|:0|o_O|:-o|:-O',       'surprise'),
    (r'v\.v',                       'tired'),
    (r':~|:-~',                     'worried'),
    (r':\\|:-\\',                   'smirk'),
    (r':\)|:-\)',                   'smile'),
    (r':\]|:-\]',                   'smile-big'),
    (r'\[ninja\]',                  'ninja'),
    (r':@|:-@',                     'angry'),
    (r'\[monkey\]',                 'monkey'),
    (r'O\.o',                       'pig'),
)

class CommentManager(models.Manager):
    def serialize(self, url):
        """ Serialize commentaries and responses for a particular URL.
        mainly used for json formated communication """
        data = _client.get('serialize:%s' % url)
        if data is not None:
            return data
        
        r = []
        for com in list(Comment.objects.filter(url=url, visible=True, trash=False, parent=None)):
            c = {
                'message': com._get_info(),
                'response': []
            }
            for resp in list(Comment.objects.filter(visible=True, trash=False, parent=com)):
                c['response'].append(resp._get_info())
            r.append(c)
            
        _client.set("serialize:%s" % url, r)
        
        return r

class Comment(models.Model):
    url = models.CharField(max_length=255, db_index=True,
                           verbose_name="Internal URL", help_text="Internal site url for the comment")
    content = models.TextField(verbose_name="Commentaire")
    submission_date = models.DateTimeField()
    parent = models.ForeignKey('Comment', db_index=True, null=True, blank=True)
    user = models.ForeignKey(AuthUser, db_index=True, null=True, blank=True, related_name="com_user")
    external_user = models.CharField(max_length=40, blank=True, null=True)
    moderate = models.BooleanField(default=False)
    visible = models.BooleanField(default=False, db_index=True)
    trash = models.BooleanField(default=False, db_index=True)
    ip = models.IPAddressField(blank=True, null=True)
    is_message = models.BooleanField(default=False)
    message_url = models.CharField(max_length=255, blank=True, null=True)
    
    likeit = models.IntegerField(default=0)
    dislikeit = models.IntegerField(default=0)
    
    objects = CommentManager()

    def save(self, *args, **kwargs):
        """ Replace links and smileys """
        
        # Does this message have a <a> tag which it means it's just a vote
        if re.search(r'<a\s+href=.*?</a>', self.content) is None:
            #self.content = striptags(self.content) + " "
            self.content += " "
            
            
            # You Tube
            self.content = re.sub(r'&feature=related', '', self.content)
            self.content = re.sub(r'http://www\.youtube\.com/watch\?v=(.{11})',NEW_YOUTUBE_CODE, self.content)
            self.content = re.sub(r'http://youtu\.be/(.{11})', NEW_YOUTUBE_CODE, self.content)
            # TODO: Get all youtube param with split("&") and just add v= 
            self.content = re.sub(r'http://www.youtube.com/watch\?feature=endscreen&NR=1&v=(.{11})', NEW_YOUTUBE_CODE, self.content)
            
            # Daily Motion
            self.content = re.sub(r'http://www\.dailymotion\.com/video/(\w+)(_.*?\s+)', NEW_DAILYMOTION_CODE, self.content)
            
            # Picts
            self.content = re.sub(r'(http://.*?\.jpg)\s','<a href="\\1" class="fancyme"><img src="\\1" style="max-width:500px" /></a><br class="clear" />', self.content, re.I)
            self.content = re.sub(r'(http://.*?\.png)\s','<a href="\\1" class="fancyme"><img src="\\1" style="max-width:500px" /></a><br class="clear" />', self.content, re.I)
            self.content = re.sub(r'(http://.*?\.gif)\s','<a href="\\1" class="fancyme"><img src="\\1" style="max-width:500px" /></a><br class="clear" />', self.content, re.I)
            
            ## remove youtube contents
            try:
                for a in re.findall(r'((http|https)://.*?)[\s+|<]', self.content):
                    print a
                    if re.search(r'dailymotion|youtu', a[0]):
                        continue
                            
                    if re.search(r'<img src="%s'% a[0], self.content):
                        continue
                
                    self.content = self.content.replace(a[0], '<a href="%s" target="_blank">%s</a>' % (a[0], a[0]))
            except:
                # FIXME: The regex crash when self.content contains "(http://address.tld)"
                pass
            
            # Check upload picture and move them
            for pict, unused_ext in re.findall(r'/site_media/temp/(.*?\.(jpg|png|jpeg|gif))\s+', self.content, re.I):
                old_path = os.path.join(settings.MEDIA_ROOT, settings.BANDCOCHON_CONFIG.Upload.temp, pict)
                new_path = os.path.join(settings.MEDIA_ROOT, settings.BANDCOCHON_CONFIG.Upload.wall, pict)
                shutil.move(old_path, new_path)
                path = os.path.join(settings.MEDIA_URL, settings.BANDCOCHON_CONFIG.Upload.wall, pict)
                self.content = self.content.replace('/site_media/temp/%s' % pict, '<a href="%s" class="fancyme"><img src="%s" class="book-image" alt="Image from %s" /></a>' % (path, path, self.user.username))
            

            # Smileys
            for smile in SMILEYS:
                if re.search(smile[0], self.content) is not None:
                    self.content = re.sub(smile[0], '<span class="icon inline-icon smiley-%s"></span>' % smile[1], self.content)
            
        self.content = linebreaksbr(self.content.strip())
        super(Comment, self).save(*args, **kwargs)
        
    class Meta:
        ordering = ("-submission_date",)
        
    def __unicode__(self):
        try:
            return self.content[:50]
        except:
            return "Une erreur est apparue"
    
    def admin_clear_trash(self):
        """ Remove all comments marked as trash """
        Comment.objects.filter(trash=True).delete()
        
    def get_absolute_url(self):
        """ Get the url on the web site """
        if self.parent is None:
            return self.url
        return self.parent.get_absolute_url()
    
    def get_response(self):
        data = _client.get('comment:get_response:%s' % self.pk)
        if data is not None:
            return data
        
        data = list(Comment.objects.filter(visible=True, trash=False, parent=self).order_by('submission_date'))
        _client.set('comment:get_response:%s' % self.pk, data)
        return data
        
    def can_set_abuse(self, user):
        """ Return True if the use is not the Comment__user owner or the 
        user have still declared this abuse """
        return CommentAbuse.objects.filter(comment=self, user=user).only('id').count() == 0
    
    def set_abuse(self, user):
        """ Set an abus (uses self moderation) """
        if self.can_set_abuse(user):
            CommentAbuse.objects.create(user=user, comment=self)
        
    def get_abuse_count(self):
        ''' Get the number of abuse for this Comment. '''
        return CommentAbuse.objects.filter(comment=self).values('pk').count()
    get_abuse_count.short_description = "Nombre d'abus"

    def get_agreeiers(self):
        data = _client.get('comment:get_agreeiers:%s' % self.pk)
        if data is not None:
            return data
        
        data = list(LikeDislike.objects.filter(comment=self, like=True, dislike=False).only('user'))
        _client.set('comment:get_agreeiers:%s' % self.pk, data)
        return data

    def get_disagreeiers(self):
        data = _client.get('comment:get_disagreeiers:%s' % self.pk)
        if data is not None:
            return data
        
        data = list(LikeDislike.objects.filter(comment=self, like=False, dislike=True).only('user'))
        _client.set('comment:get_disagreeiers:%s' % self.pk, data)
        return data

    def _get_info(self):
        """ return the row as a dictionnary """
        return {
            'content': self.content,
            'submission_date': convert_date(self.submission_date),
            'user' : self.user.username,
            'external_user': self.external_user,
            'avatar' : self.user.get_profile().avatar_or_default(),
        }
        