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

import datetime
import json
import os
import re
import hashlib

from PIL import Image

from django.contrib.auth.decorators import login_required
from django.template import loader, RequestContext
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.sites.models import Site
from django.conf import settings
from django.db.models import Q
from django.middleware.csrf import get_token

from bandcochon.models import Picture
from ucomment.models import Comment, LikeDislike, CommentPref, CommentAbuse

from notification import ajax_log, notification_send, Notification
from common import convert_date


def postmessage(request):
    """ Post a message as AJAX """
    try:
        if request.method == 'POST' and request.is_ajax():
            # FIXME : CommentPref.get_pref
            if CommentPref.get_pref().only_registred == True and request.user.is_authenticated() == False:
                ajax_log('ucomment.views.postmessage: Try to post when not authenticated. IP address: %s' % request.META['REMOTE_ADDR'])
                return HttpResponseBadRequest('')

            parent = request.POST.get('parent', None)
            if parent is not None:
                parent = Comment.objects.get(pk=parent)
                                
            content = request.POST['content']
            
            onwallurl = request.POST.get('onwallurl', False)
            if len(content) > 0:
                referer = request.POST.get('referer', '/')
                if len(referer) == 0:
                    referer = "/"
                
                if onwallurl != False and referer == '/' and onwallurl != '/':
                    referer = request.META['HTTP_REFERER'].replace('http://%s' % Site.objects.get_current().domain, '')

                comment = Comment.objects.create(
                    url=referer,
                    content=content,
                    submission_date=datetime.datetime.now(),
                    visible=CommentPref.get_pref().publish_on_submit,
                    ip=request.META['REMOTE_ADDR'],
                    user=request.user,
                    parent=parent
                )
                
                # Prepare JSON
                d = {
                    'username' : request.user.username,
                    'submission_date': convert_date(datetime.datetime.now()),
                    'knowuser' : True,
                    'avatar' : request.user.get_profile().avatar_or_default(),
                    'userid' : request.user.id,
                    'commentcount': Comment.objects.filter(user=request.user, visible=True, moderate=False).only('id').count(),
                    'pigstiescount': Picture.objects.filter(user=request.user, trash=False).only('id').count(),
                    'content' : comment.content,
                    'commentid' : comment.id,
                    'user_authenticated' : request.user.is_authenticated(),
                    'csrf_token' : get_token(request),
                }
                
                if parent is not None:
                    d['parentid'] = parent.id
                else:
                    d['parentid'] = comment.id
                    
                # Send a email to all users
                if parent is not None:
                    comments = list(Comment.objects.filter(Q(parent=parent) & ~Q(user=request.user)).only('user__email'))
#                    comments = list(Comment.objects.filter(Q(parent=parent)).only('user__email'))
                    mails = {}
                    for comment in comments:
                        mails[comment.user.email] = ''
                    req = RequestContext(request, {
                        'username':  request.user.username,
                        'message' : comment.content,
                        'url' : comment.url
                    })
                    if settings.IS_LOCAL == False and settings.IS_TESTING == False:
                        notif = Notification(settings.BANDCOCHON_CONFIG.EmailTemplates.user_comment)
                        for mail in mails.keys():
                            notif.push(mail, req)
                        notif.send()
                    else:
                        ajax_log("DEBUG MODE : I have to send an email to %s " % mails.keys())
                # Send Json
                return HttpResponse(json.dumps(d), mimetype="application/json")
        else:
            ajax_log("ucomment.views.postmessage: Not an AJAX call : %s" % request.META['REMOTE_ADDR'])
            
    except Exception as e:
        ajax_log("ucomment.views.postmessage : %s: IP : %s" % (e, request.META['REMOTE_ADDR']))

    return HttpResponseBadRequest('')

def agree(request):
    """ Agree a comment
    @TODO: Translate messages
    """
    try:
        if request.is_ajax() and request.method == 'POST':
            if not request.user.is_authenticated() and CommentPref.get_pref().only_registred == True:
                return HttpResponse("""{"success":false, "message":"Vous devez vous enregistrer pour voter"}""",
                                    mimetype="application/json")
            
            comment = Comment.objects.get(pk=request.POST['message'])
            if (comment.user == request.user):
                return HttpResponse("""{"success":false, "message":"Vous ne pouvez pas voter pour vous même !!"}""",
                                    mimetype="application/json")
                
            if LikeDislike.objects.filter(comment=comment, user=request.user).count() > 0:
                return HttpResponse('''{"success":false, "message":"Vous ne pouvez plus voter pour ce message"}''',
                                    mimetype="application/json")
                
            LikeDislike.objects.create(
                user=request.user,
                comment=comment,
                like=True
            )

            comment.likeit += 1
            comment.save()
            
            if comment.user.get_profile().accept_notification == True and settings.IS_LOCAL == False and settings.IS_TESTING == False:
                notification_send(settings.BANDCOCHON_CONFIG.EmailTemplates.user_like, comment.user.email, RequestContext(request, {
                    'username' : request.user.username,
                    'message' : comment.content,
                    'url' : comment.get_absolute_url()
                }))
            else:
                ajax_log("DEBUG MODE : I have to send a email")
                
            agreeiers = []
            for u in comment.get_agreeiers():
                agreeiers.append({
                    'username' : u.user.username,
                    'avatar': u.user.get_profile().avatar_or_default()
                })

            return HttpResponse("""{"success": true, "message": "Votre vote a été pris en compte", "agreeiers" : %s}""" % json.dumps(agreeiers), mimetype="application/json")
        else:
            ajax_log("ucomment.views.agree: Not an ajax or a post ; %s" % request.META['REMOTE_ADDR'])
    except Exception as error:
        ajax_log("ucomment.views.agree : %s: IP : %s" % (error, request.META['REMOTE_ADDR']))
    
    return HttpResponseBadRequest('')
    
def disagree(request):
    """ Disagree a comment """
    try:
        if request.is_ajax() and request.method == 'POST':
            if not request.user.is_authenticated():
                return HttpResponse("""{"success":false, "message":"Vous devez vous enregistrer pour voter"}""", mimetype="application/json")

            comment = Comment.objects.get(pk=request.POST['message'])
            if (comment.user == request.user):
                return HttpResponse("""{"success":false, "message":"Vous ne pouvez pas voter pour vous même !!"}""", mimetype="application/json")
                
            if LikeDislike.objects.filter(comment=comment, user=request.user).count() > 0:
                return HttpResponse('''{"success":false, "message":"Vous ne pouvez plus voter pour ce message"}''', mimetype="application/json")
            
            LikeDislike.objects.create(
                user=request.user,
                comment=comment,
                dislike=True
            )
            
            comment.dislikeit += 1
            comment.save()

            if comment.user.get_profile().accept_notification == True and settings.IS_LOCAL == False and settings.IS_TESTING == False:
                notification_send(settings.BANDCOCHON_CONFIG.EmailTemplates.user_dislike, comment.user.email, RequestContext(request, {
                    'username' : request.user.username,
                    'message' : comment.content,
                    'url' : comment.get_absolute_url()
                }))
            else:
                ajax_log("DEBUG MODE : I have to send a email")
                
            disagreeiers = []
            for u in comment.get_disagreeiers():
                disagreeiers.append({
                    'username' : u.user.username,
                    'avatar': u.user.get_profile().avatar_or_default()
                })
            return HttpResponse("""{"success": true, "message": "Votre vote a été pris en compte", "disagreeiers" : %s}""" % json.dumps(disagreeiers), mimetype="application/json")
        else:
            ajax_log("ucomment.views.disagree: Not an ajax or a post ; %s" % request.META['REMOTE_ADDR'])
            
    except Exception as error:
        ajax_log("ucomment.views.disagree : %s: IP : %s " % (error, request.META['REMOTE_ADDR']))
    return HttpResponseBadRequest('')
    
    
@login_required
def moderate(request):
    """ Moderate a comment """
    try:
        if request.is_ajax():
            if request.method == 'POST':
                comment = Comment.objects.get(pk=request.POST['rel'])
                abuse_max = int(CommentPref.get_pref().abuse_max)
                if request.user.is_staff:
                        comment.moderate = True
                else:
                    if comment.can_set_abuse(request.user):
                        if comment.get_abuse_count() < abuse_max:
                            CommentAbuse(comment=comment, user=request.user).save()
                        if comment.get_abuse_count() >= abuse_max:
                            comment.moderate = True
                    else:
                        comment.moderate = True
                comment.save()
                return HttpResponse('')
    except Exception as e:
        ajax_log("ucomment.views.moderate : %s : IP : %s" % (e, request.META['REMOTE_ADDR']))
    return HttpResponseBadRequest('')

def nextcomment(request):
    """ Get next comments """
    try:
        if request.is_ajax():
            if request.method == 'GET':
                startat = int(request.GET['startat'])
                url = request.GET['url']
                a = Comment.objects.filter(url=url, visible=True, trash=False, parent=None, is_message=False)[startat:startat + 15]
                context = RequestContext(request, {
                    'commentaries': a[:15],
                    'ucomment': {'total_count': Comment.objects.filter(url=url, visible=True, trash=False).values_list('pk').count()}
                })
                return HttpResponse(loader.get_template("ucomment/messageblock.html").render(context))
    except Exception as e:
        ajax_log("nextcomment : %s" % e)
    return HttpResponseBadRequest('')
                        
def showlast(request):
    try:
        if request.is_ajax():
            if request.method == 'GET':
                startat = request.GET['startat']
                last = request.GET['last']
                url = request.GET['url']
                context = RequestContext(request, {
                    'commentaries':  Comment.objects.filter(url=url, visible=True, trash=False, pk__lte=last)[startat:startat + 15],
                    'ucomment': {'total_count' : Comment.objects.filter(url=url, visible=True, trash=False).values_list('pk').count()}
                })
                return HttpResponse(loader.get_template('ucomment/messageblock.html').render(context))
    except Exception as e:
        ajax_log("showlast : %s" % e)
    
    return HttpResponseBadRequest('')
    
@login_required
def sendphoto(request):
    """ Send a picture, storeit into temp directory """
    datarel = 0
    try:
        if request.method == 'POST':
            keys = request.FILES.keys()
            if len(keys) == 1:
                # Get informations
                fileobj = request.FILES.get(keys[0])
                picture_name = fileobj.name
                datarel = keys[0][5:]
                if keys[0][:-len(datarel)] != 'photo':
                    # Ensure the fieldname (minimal security - not really useful)
                    return HttpResponse("""<script type="text/javascript">window.top.window.imageUploaded('Une erreur est survenue', 0, true);</script>""")
                    
                # prepare names
                if not re.search(r'jpg|jpeg|png|gif', picture_name, re.I):
                    return HttpResponse('''<script type="text/javascript">window.top.window.imageUploaded("Ce type de fichier n'est pas autoris&eacute;", %s, true);</script>''' % datarel)
                
                unused_name, ext = os.path.splitext(picture_name)
                dest_name = "%s%s" % (hashlib.sha1(request.user.username + datetime.datetime.now().strftime("%s")).hexdigest(), ext)
                dest_dir = os.path.join(settings.MEDIA_ROOT, settings.BANDCOCHON_CONFIG.Upload.temp, dest_name)
                relative_path = os.path.join(settings.MEDIA_URL, settings.BANDCOCHON_CONFIG.Upload.temp, dest_name)
    
                # download picture
                f = open(dest_dir, "wb+")
                for chunk in fileobj.chunks():
                    f.write(chunk)
                f.close()
                
                # Reduce it
                image = Image.open(dest_dir)
                image.thumbnail((1024, 768))
                image.save(dest_dir)
    
                # Send response
                return HttpResponse("""<script type="text/javascript">window.top.window.imageUploaded('%s', %s, false);</script>""" % (relative_path, datarel))
        else:
            ajax_log('ucomment.views.sendphoto: Get method : %s' % request.META['REMOTE_ADDR'])
    except Exception as e:
        ajax_log("ucomment.views.sendphoto: Error : %s : %s" % (e, request.META['REMOTE_ADDR']))
        
    return HttpResponse("""<script type="text/javascript">window.top.window.imageUploaded('Une erreur est survenue', %s, true);</script>""" % datarel)
    
