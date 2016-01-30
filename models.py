# -*- coding: UTF-8 -*-
# UComment - Django Universal Comment
# (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>
#

import locale
import re
import shutil
import os

from django.utils.translation import ugettext_lazy as _
from django.db import models, connection
from django.contrib.auth.models import User as AuthUser
from django.template.defaultfilters import linebreaksbr
from django.conf import settings
from django.core.cache import cache


def convert_date(value):
    """ replace month because strftime is not unicode compliant """
    return value.strftime("%d %B %Y").decode(locale.getpreferredencoding())


class CommentPrefManager(models.Manager):
    def get_preferences(self):
        """ Return preferences for Comment. Create with default values if not exists """
        return self.get_queryset().lastest('id') if self.get_queryset().count() > 0 else CommentPref.objects.create()


class CommentPref(models.Model):
    """ Preferences for UComment """
    only_registred = models.BooleanField(
        default=True,
        verbose_name=_("Only registred"),
        help_text=_("Only registred user can post (if no, every body can post)")
    )

    use_like_dislike = models.BooleanField(
        default=True,
        verbose_name=_("Use Like Dislike"),
        help_text=_("Use the like and dislike system.")
    )

    # TODO: Remove this
    publish_on_submit = models.BooleanField(
        default=True
    )

    register_ip = models.BooleanField(
        default=True,
        verbose_name=_("Register IP"),
        help_text=_("Save IP address on each post")
    )

    abuse_max = models.SmallIntegerField(
        default=3,
        verbose_name=_("Maximum abuse"),
        help_text=_("Maximum abuse count before moderation")
    )

    # TODO: Remove this
    use_notification = models.BooleanField(
        default=False,
        verbose_name="Notification",
        help_text=u"Use notification inside the Wall"
    )

    objects = CommentPrefManager()

    def __unicode__(self):
        return "Comment Preferences : #%d" % self.pk

    class Meta:
        app_label = "ucomment"


class CommentAbuse(models.Model):
    user = models.ForeignKey(AuthUser)
    comment = models.ForeignKey('Comment')

    class Meta:
        app_label = "ucomment"


class LikeDislike(models.Model):
    comment = models.ForeignKey("Comment")
    like = models.BooleanField(default=False, db_index=True)
    dislike = models.BooleanField(default=False, db_index=True)
    user = models.ForeignKey(AuthUser, db_index=True, null=True, blank=True, related_name="ld_user")

    def __unicode__(self):
        return self.comment.url

    class Meta:
        app_label = "ucomment"


NEW_YOUTUBE_CODE = '''<div class="videocontainer"><iframe width="560" height="315" src="https://www.youtube.com/embed/\\1" frameborder="0" allowfullscreen></iframe></div>'''
NEW_DAILYMOTION_CODE = '''<div class="videocontainer"><iframe frameborder="0" width="560" height="315" src="http://www.dailymotion.com/embed/video/\\1"></iframe></div><br>'''

SMILEYS = (
    (r'O:\)|O:-\)', 'angel'),
    (r':p|:-p', 'raspberry'),
    (r';\)|;-\)', 'wink'),
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


class CommentManager(models.Manager):
    def getForParent(self, parent):
        data = cache.get('get_for_parent-%s' % parent.url)
        if data is None:
            data = list(super(CommentManager, self).get_queryset().filter(parent=parent, visible=True, trash=False))
            cache.set('get_for_parent-%s' % parent.url, data)
        return cache

    def getForUrl(self, url, count=-1):
        """
        Get last comments for the url
        """
        if count == -1:
            # Get all
            comments = list(self.get_queryset().filter(visible=True, trash=False, url=url, parent=None))
        else:
            comments = list(self.get_queryset().filter(visible=True, trash=False, url=url, parent=None)[:count])

        # Get and regroup sons
        comments_son = {}
        for cs in list(self.get_queryset().filter(parent__in=[comment.pk for comment in comments]).order_by('submission_date')):
            if not cs.parent.pk in comments_son:
                comments_son[cs.parent.pk] = []
            comments_son[cs.parent.pk].append(cs)

        # Attribute sons to parents
        for com in comments:
            if com.pk in comments_son:
                com.get_response = comments_son[com.pk]
            else:
                com.get_response = None

        return comments

    def get_for_url(self, url, count=-1):
        return self.getForUrl(url, count)

    def serialize(self, url):
        """ Serialize commentaries and responses for a particular URL.
        mainly used for json formated communication """
        result = []
        for com in list(Comment.objects.filter(url=url, visible=True, trash=False, parent=None)):
            comment = {
                'message': com._get_info(),
                'response': []
            }

            for resp in list(Comment.objects.filter(visible=True, trash=False, parent=com)):
                comment['response'].append(resp._get_info())

            result.append(comment)

        return result

    def get_with_children(self, url, limit=0):
        """
        Get all comments for the URL and the children too
        """
        result = []
        cursora = connection.cursor()
        cursorb = connection.cursor()
        if limit > 0:
            limit = "LIMIT %d" % int(limit)
        else:
            limit = ''
        cursora.execute("""
        SELECT co.id, co.submission_date, au.username, co.content, ut.avatar
        FROM ucomment_comment co, auth_user au, bandcochon_utilisateur ut
        WHERE co.url='%s' AND co.visible=1 AND co.user_id=au.id AND ut.user_id=au.id
        ORDER BY co.submission_date DESC %s""" % (url, limit))
        cols = [d[0] for d in cursora.description]
        for com in cursora.fetchall():
            com = list(com)
            com[1] = convert_date(com[1])
            parent = dict(zip(cols, com))
            parent['like'], parent['dislike'] = self._get_like_dislike_for(parent['id'])

            cursorb.execute("""
            SELECT co.id, co.submission_date, au.username, co.content
            FROM ucomment_comment co, auth_user au
            WHERE co.url='%s' AND co.visible=1 AND co.user_id=au.id
            """ % parent['id'])
            children = []
            for child in cursorb.fetchall():
                child = list(child)
                child[1] = convert_date(child[1])
                child_ = dict(zip(cols, child))
                child_['like'], child_['dislike'] = self._get_like_dislike_for(child_['id'])
                children.append(child_)
            parent['responses'] = children
            result.append(parent)
        return result

    def _get_like_dislike_for(self, id_):
        """
        Return like and dislike for a message
        """
        cursor = connection.cursor()
        cursor.execute("""
        SELECT     au.username, ut.avatar
        FROM       ucomment_likedislike ud
        INNER JOIN auth_user au ON(ud.user_id=au.id)
        INNER JOIN bandcochon_utilisateur ut ON(au.id=ut.user_id)
        WHERE ud.comment_id='%d' AND ud.like='1' """ % id_)
        cols = [d[0] for d in cursor.description]
        likeit = [dict(zip(cols, row)) for row in cursor.fetchall()]

        cursor.execute("""
        SELECT     au.username, ut.avatar
        FROM       ucomment_likedislike ud
        INNER JOIN auth_user au ON(ud.user_id=au.id)
        INNER JOIN bandcochon_utilisateur ut ON(au.id=ut.user_id)
        WHERE ud.comment_id='%d' AND ud.dislike='1' """ % id_)
        dislike_it = [dict(zip(cols, row)) for row in cursor.fetchall()]

        return likeit, dislike_it


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
    ip = models.GenericIPAddressField(blank=True, null=True)
    is_message = models.BooleanField(default=False)
    message_url = models.CharField(max_length=255, blank=True, null=True)

    likeit = models.IntegerField(default=0)
    dislikeit = models.IntegerField(default=0)

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
            self.content = re.sub(r'(http://.*?\.jpg)\s',
                                  '<a href="\\1" class="fancyme"><img src="\\1" style="max-width:500px" /></a><br class="clear" />',
                                  self.content, re.I)
            self.content = re.sub(r'(http://.*?\.png)\s',
                                  '<a href="\\1" class="fancyme"><img src="\\1" style="max-width:500px" /></a><br class="clear" />',
                                  self.content, re.I)
            self.content = re.sub(r'(http://.*?\.gif)\s',
                                  '<a href="\\1" class="fancyme"><img src="\\1" style="max-width:500px" /></a><br class="clear" />',
                                  self.content, re.I)

            ## remove youtube contents
            try:
                for found in re.findall(r'((http|https)://.*?)[\s+|<]', self.content):
                    if re.search(r'dailymotion|youtu', found[0]):
                        continue

                    if re.search(r'<img src="%s' % found[0], self.content):
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

    def get_disagreeiers(self):
        return list(LikeDislike.objects.filter(comment=self, like=False, dislike=True).only('user'))

    def _get_info(self):
        """ return the row as a dictionnary """
        return {
            'content': self.content,
            'submission_date': convert_date(self.submission_date),
            'user': self.user.username,
            'external_user': self.external_user,
            'avatar': self.user.get_profile().avatar_or_default(),
        }
