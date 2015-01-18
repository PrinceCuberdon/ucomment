# -*- coding: UTF-8 -*-
# UComment - Django Universal Comment
# (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>
#

import re
import shutil
import os

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User as AuthUser
from django.conf import settings
from django.template.defaultfilters import linebreaksbr

from .commentmanager import CommentManager


NEW_YOUTUBE_CODE = '''
<div class="videocontainer">
    <iframe width="560" height="315" src="https://www.youtube.com/embed/\\1" frameborder="0" allowfullscreen>
    </iframe>
</div>
'''

NEW_DAILYMOTION_CODE = '''
<div class="videocontainer">
    <iframe frameborder="0" width="560" height="315" src="http://www.dailymotion.com/embed/video/\\1">
    </iframe>
</div>
<br/>
'''

SMILEYS = (
    (r'O:\)|O:-\)', 'angel'),
    (r':p|:-p', 'raspberry'),
    (r';\)|;-\)', 'wink'),
    ##(r'\^8\^', 'bat'),
    (r'\>:\)|\>:-\)|\]:-\)|\]:\)', 'devilish'),
    (r'8\||8-\||B\)|B-\)', 'cool'),
    (r":'\(|:'-\(", 'crying'),
    (r':\$', 'embarrassed'),
    (r'8\)|8-\)', 'glasses'),
    (r':\*|:-\*', 'kiss'),
    (r':D|:-D', 'laugh'),
    (r':\||:-\|', 'uncertain'),
    (r':\(|:-\(', 'sad'),
    (r'\+o\(', 'sick'),
    (r':o|:O|:0|o_O|:-o|:-O', 'surprise'),
    (r'v\.v', 'tired'),
    (r':~|:-~', 'worried'),
    (r':\\|:-\\', 'smirk'),
    (r':\)|:-\)', 'smile'),
    (r':\]|:-\]', 'smile-big'),
    (r'\[ninja\]', 'ninja'),
    (r':@|:-@', 'angry'),
    (r'\[monkey\]', 'monkey'),
    (r'O\.o', 'pig'),
)


class Comment(models.Model):
    """
    Model for a comment
    """
    
    # On wich page the comment was emitted.
    # The default is root page
    url = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name=_("Internal URL"),
        help_text=_("Internal site url for the comment")
    )
    
    # The comment content
    content = models.TextField(
        verbose_name="Commentaire"
    )
    
    # When the comment was emitted
    submission_date = models.DateTimeField()
    
    # Who is the parent of this comment (must be a comment)
    parent = models.ForeignKey(
        'self',
        db_index=True,
        null=True,
        blank=True
    )
    
    # Who is the user that emitted the comment
    user = models.ForeignKey(
        AuthUser,
        db_index=True,
        null=True,
        blank=True,
        related_name="com_user"
    )
    
    external_user = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        default=''
    )
    
    abuse_count = models.SmallIntegerField(
        default=0
    )
    
    moderate = models.BooleanField(
        default=False
    )
    
    visible = models.BooleanField(
        default=False,
        db_index=True
    )
    
    trash = models.BooleanField(
        default=False,
        db_index=True
    )
    
    ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        default=''
    )
    
    likeit = models.IntegerField(
        default=0
    )
    
    dislikeit = models.IntegerField(
        default=0
    )

    objects = CommentManager()

    def save(self, *args, **kwargs):
        """ Replace links and smileys """
        # Does this message have a <a> tag which it means it's just a vote
        if re.search(r'<a\s+href=.*?</a>', self.content) is None:
            self.content += " "

            # You Tube
            self.content = re.sub(r'&feature=related', '', self.content)
            self.content = re.sub(r'[http|https]://www\.youtube\.com/watch\?v=(.{11})', NEW_YOUTUBE_CODE, self.content)
            self.content = re.sub(r'http://youtu\.be/(.{11})', NEW_YOUTUBE_CODE, self.content)
            # TODO: Get all youtube param with split("&") and just add v=
            self.content = re.sub(r'http://www.youtube.com/watch\?feature=endscreen&NR=1&v=(.{11})',
                                  NEW_YOUTUBE_CODE, self.content)

            # Daily Motion
            self.content = re.sub(r'http://www\.dailymotion\.com/video/(\w+)(_.*?\s+)',
                                  NEW_DAILYMOTION_CODE, self.content)

            # Picts
            self.content = re.sub(
                r'(http://.*?\.jpg)\s',
                '<a href="\\1" class="fancyme"><img src="\\1" style="max-width:500px" /></a><br class="clear" />',
                self.content, re.I
            )

            self.content = re.sub(
                r'(http://.*?\.png)\s',
                '<a href="\\1" class="fancyme"><img src="\\1" style="max-width:500px" /></a><br class="clear" />',
                self.content, re.I
            )
            self.content = re.sub(r'(http://.*?\.gif)\s',
                                  '<a href="\\1" class="fancyme"><img src="\\1" style="max-width:500px" /></a><br class="clear" />',
                                  self.content, re.I)

            ## remove youtube contents
            try:
                for found in re.findall(r'((http|https)://.*?)[\s+|<]', self.content):
                    if re.search(r'dailymotion|youtu', found[0]):
                        continue

                    if re.search(r'<img src="%s'% found[0], self.content):
                        continue

                    self.content = self.content.replace(found[0], '<a href="%s" target="_blank">%s</a>' %
                                                        (found[0], found[0]))
            except:
                # FIXME: The regex crash when self.content contains "(http://address.tld)"
                pass

            # Check upload picture and move them
            for pict, _ext in re.findall(r'/site_media/temp/(.*?\.(jpg|png|jpeg|gif))\s+', self.content, re.I):
                old_path = os.path.join(settings.MEDIA_ROOT, settings.BANDCOCHON_CONFIG.Upload.temp, pict)
                new_path = os.path.join(settings.MEDIA_ROOT, settings.BANDCOCHON_CONFIG.Upload.wall, pict)
                shutil.move(old_path, new_path)
                path = '/'.join([settings.MEDIA_URL, settings.BANDCOCHON_CONFIG.Upload.wall, pict]).replace('//', '/')
                self.content = self.content.replace('/site_media/temp/%s' % pict,
                                                    '<a href="%s" class="fancyme"><img src="%s" class="book-image" alt="Image from %s" /></a>'
                                                    % (path, path, self.user.username))
            # Smileys
            for smile in SMILEYS:
                if re.search(smile[0], self.content) is not None:
                    self.content = re.sub(smile[0],
                                          '<span class="icon inline-icon smiley-%s"></span>' % smile[1], self.content)

        self.content = linebreaksbr(self.content.strip())
        super(Comment, self).save(*args, **kwargs)

    class Meta:
        ordering = ("-submission_date",)
        app_label = "ucomment"
        

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

    # def get_response(self):
    #     return list(Comment.objects.filter(visible=True, trash=False, parent=self).order_by('submission_date'))

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
        return list(LikeDislike.objects.filter(comment=self, like=True, dislike=False).only('user'))
    get_likers = get_agreeiers
    
    def get_disagreeiers(self):
        return list(LikeDislike.objects.filter(comment=self, like=False, dislike=True).only('user'))
    get_dislikers = get_disagreeiers
    
    def _get_info(self):
        """ return the row as a dictionnary """
        return {
            'content': self.content,
            'submission_date': convert_date(self.submission_date),
            'user' : self.user.username,
            'external_user': self.external_user,
            'avatar' : self.user.get_profile().avatar_or_default(),
        }

