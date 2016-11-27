# -*- coding: UTF-8 -*-
# UComment - Universal Comment
# A Django based application for commentaries
#
# (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>

import hashlib
import time
import logging
import os
import re

from PIL import Image
from django.contrib.auth.decorators import login_required
from django.template import loader, RequestContext
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.contrib.sites.models import Site
from django.conf import settings
from django.db.models import Q
from django.middleware.csrf import get_token
from django.shortcuts import render_to_response, render
from django.views.generic import TemplateView
from django.utils import timezone

from core.bandcochon.models import Picture
from .models import Comment, LikeDislike, CommentPref, CommentAbuse
from notification import notification_send, Notification
from core.common import convert_date
import ucomment

L = logging.getLogger("bandcochon")


class BookView(TemplateView):
    template_name = settings.UCOMMENT_TEMPLATE

    def get_context_data(self, **kwargs):
        # Call the context
        L.info("Load 25 comments for the root URL")

        context = super(BookView, self).get_context_data(**kwargs)
        context['book_comments'] = ucomment.api.get_comments('/', 25)
        context['display_conn'] = True

        return context


class BookViewNext(TemplateView):
    template_name = settings.UCOMMENT_NEXT_TEMPLATE

    def get(self, request, *args, **kwargs):
        L.info("Get next 25 comments for the root url")

        count = int(request.GET.get('from')) - 1
        comments = list(Comment.objects.filter(visible=True, trash=False, url='/', parent=None)[count + 1:count + 25])
        return render(request, {
            'url': '/',
            'book_comments': list(comments),
            'display_conn': False
        })


def book_next(request):
    """ Get next messages on the wall as JSON """
    L.info("ucomment.views.book_next : Get next 25 comments for the root url")

    if request.method == "GET":
        count = int(request.GET.get('from', 0)) - 1
        comments = list(Comment.objects.filter(visible=True, trash=False, url='/', parent=None)[count + 1:count + 25])
        L.info("ucomment.views.book_next: render the next 25 messages")

        return render_to_response('inc/book.html', RequestContext(request, {
            'url': '/',
            'book_comments': list(comments),
            'display_conn': False
        }))

    L.error("ucomment.views.book_next : Not a AJAX call or GET method")
    return HttpResponseBadRequest('')


def postmessage(request):
    """ Post a message as AJAX """
    remote_addr = request.META.get('REMOTE_ADDR')
    http_referer = request.META.get('HTTP_REFERER')

    L.info("Post a message from {remote} for the page {referer}".format(remote=remote_addr, referer=http_referer))

    if request.method == 'POST':
        if CommentPref.objects.get_preferences().only_registred and not request.user.is_authenticated():
            L.error('ucomment.views.postmessage: Try to post when not authenticated. ')
            return HttpResponseBadRequest('')

        parent = int(request.POST.get('parent'))
        parent = Comment.objects.get(pk=parent) if parent != 0 else None
        content = request.POST['content']
        onwallurl = request.POST.get('onwallurl')

        if content:
            referer = request.POST.get('url')
            if not referer:
                referer = "/"

            if not onwallurl and referer == '/' and onwallurl != '/':
                referer = http_referer.replace('http://%s' % Site.objects.get_current().domain, '')

            # comment = Comment.objects.create(
            comment = Comment.objects.post_comment(
                url=referer,
                message=content,
                raw_html=False,
                user=request.user,
                ip=remote_addr,
                parent=parent
            )

            # Prepare JSON
            data = {
                'username': request.user.username,
                'submission_date': convert_date(timezone.now()),
                'knowuser': True,
                'avatar': request.user.profile.avatar_or_default(),
                'userid': request.user.id,
                'commentcount': Comment.objects.filter(user=request.user, visible=True, moderate=False).only('id').count(),
                'pigstiescount': Picture.objects.filter(user=request.user, trash=False).only('id').count(),
                'content': comment.content,
                'commentid': comment.id,
                'user_authenticated': request.user.is_authenticated(),
                'csrf_token': get_token(request),
            }

            if parent is not None:
                data['parentid'] = parent.id
            else:
                data['parentid'] = comment.id

            # Send a email to all users
            if parent is not None:
                comments = list(Comment.objects.filter((Q(parent=parent) & ~Q(user=request.user))).only('user__email'))
                mails = {}
                for comment in comments:
                    mails[comment.user.email] = ''

                req = RequestContext(request, {
                    'username': request.user.username,
                    'message': comment.content,
                    'url': comment.url
                })

                if not settings.IS_LOCAL:
                    notif = Notification(settings.BANDCOCHON_CONFIG.EmailTemplates.user_comment)
                    for mail in mails.keys():
                        notif.push(mail, req)
                    notif.send()

            # Send Json
            return JsonResponse(data)
        else:
            L.error("ucomment.views.postmessage : Don't have a content message")
    else:
        L.error("ucomment.views.postmessage: Not a POST call :")

    return HttpResponseBadRequest('')


def agree(request):
    """ Agree a comment
    @TODO: Translate messages
    """
    remote_addr = request.META.get('REMOTE_ADDR')
    L.info("Agree from {remote}".format(remote=remote_addr))

    try:
        if request.method == 'POST':
            if not request.user.is_authenticated() and CommentPref.objects.get_preferences().only_registred:
                L.error("ucomment.views.agree : Agree and not registred. IP={0}".format(remote_addr))
                return JsonResponse({"success": False, "message": "Vous devez vous enregistrer pour voter"})

            comment = Comment.objects.get(pk=request.POST['message'])
            if comment.user == request.user:
                L.critical("ucomment.views.agree : Try to agree himself. IP={0}".format(remote_addr))
                return JsonResponse({"success": False, "message": "Vous ne pouvez pas voter pour vous même !!"})

            if LikeDislike.objects.filter(comment=comment, user=request.user).count() > 0:
                L.error("ucomment.views.agree : Can't vote for this message anymore. IP={0}".format(remote_addr))
                return JsonResponse({"success": False, "message": "Vous ne pouvez plus voter pour ce message"})

            LikeDislike.objects.create(user=request.user, comment=comment, like=True)

            comment.likeit += 1
            comment.save()

            if comment.user.profile.accept_notification and not settings.IS_LOCAL:
                notification_send(settings.BANDCOCHON_CONFIG.EmailTemplates.user_like,
                                  comment.user.email,
                                  RequestContext(request, {
                                      'username': request.user.username,
                                      'message': comment.content,
                                      'url': comment.get_absolute_url()
                                  }))

            agreeiers = []
            for u in comment.get_agreeiers():
                agreeiers.append({
                    'username': u.user.username,
                    'avatar': u.user.profile.avatar_or_default()
                })

            L.info("ucomment.views.agree : Voting. IP={0}".format(remote_addr))
            return JsonResponse({"success": True, "message": "Votre vote a été pris en compte", "agreeiers": agreeiers}, safe=False)
        else:
            L.error("ucomment.views.agree: Not an ajax or a post")

    except Exception as error:
        L.error("ucomment.views.agree : {error}: IP : {ip}".format(error=error, ip=remote_addr))

    L.error("Je ne comprends pas bien")
    return HttpResponseBadRequest('')


def disagree(request):
    """ Disagree a comment """
    remote_addr = request.META.get('REMOTE_ADDR')
    L.info("Disagree from {remote}".format(remote=remote_addr))

    try:
        if request.method == 'POST':
            if not request.user.is_authenticated():
                L.error("ucomment.views.disagree : Disagree and not registred. IP={0}".format(remote_addr))
                return JsonResponse({"success": False, "message": "Vous devez vous enregistrer pour voter"})

            comment = Comment.objects.get(pk=request.POST['message'])
            if comment.user == request.user:
                L.critical("ucomment.views.disagree : Try to disaagree himself. IP={0}".format(remote_addr))
                return JsonResponse({"success": False, "message": "Vous ne pouvez pas voter pour vous m&ecirc;me !!"})

            if LikeDislike.objects.filter(comment=comment, user=request.user).count() > 0:
                L.error("ucomment.views.disagree : Can't vote for this message anymore. IP={0}".format(remote_addr))
                return JsonResponse({"success": False, "message": "Vous ne pouvez plus voter pour ce message"})

            LikeDislike.objects.create(
                user=request.user,
                comment=comment,
                dislike=True
            )

            comment.dislikeit += 1
            comment.save()

            if comment.user.profile.accept_notification and not settings.IS_LOCAL:
                notification_send(settings.BANDCOCHON_CONFIG.EmailTemplates.user_dislike, comment.user.email, RequestContext(request, {
                    'username': request.user.username,
                    'message': comment.content,
                    'url': comment.get_absolute_url()
                }))

            disagreeiers = []
            for u in comment.get_disagreeiers():
                disagreeiers.append({
                    'username': u.user.username,
                    'avatar': u.user.profile.avatar_or_default()
                })

            L.info("ucomment.views.disagree : Voting. IP={0}".format(remote_addr))
            return JsonResponse({"success": True, "message": "Votre vote a été pris en compte", "disagreeiers": disagreeiers}, safe=False)

        else:
            L.error("ucomment.views.disagree: Not an ajax or a post ")

    except Exception as error:
        L.error("ucomment.views.disagree : {error}: IP : {ip} ".format(error=error, ip=remote_addr))

    return HttpResponseBadRequest('')


@login_required
def moderate(request):
    """ Moderate a comment """
    remote_addr = request.META.get('REMOTE_ADDR')
    L.info("Ask moderation from {remote}".format(remote=remote_addr))

    try:
        if request.method == 'POST':
            comment = Comment.objects.get(pk=request.POST['rel'])
            abuse_max = int(CommentPref.objects.get_preferences().abuse_max)
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
        L.error("ucomment.views.moderate : {error} : IP : {ip}".format(error=e, ip=remote_addr))
    return HttpResponseBadRequest('')


def nextcomment(request):
    """ Get next comments """
    L.info("Get next comment")

    try:
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
        L.error("nextcomment : {error}".format(error=e))
    return HttpResponseBadRequest('')


def showlast(request):
    L.info("Get the last comment")

    try:
        if request.method == 'GET':
            startat = request.GET['startat']
            last = request.GET['last']
            url = request.GET['url']
            context = RequestContext(request, {
                'commentaries': Comment.objects.filter(url=url, visible=True, trash=False, pk__lte=last)[startat:startat + 15],
                'ucomment': {
                    'total_count': Comment.objects.filter(url=url, visible=True, trash=False).values_list('pk').count()
                }
            })
            return HttpResponse(loader.get_template('ucomment/messageblock.html').render(context))
    except Exception as e:
        L.error("showlast : {error}".format(error=e))

    return HttpResponseBadRequest('')


@login_required
def sendphoto(request):
    """ Send a picture, storeit into temp directory """
    remote_addr = request.META.get('REMOTE_ADDR')
    L.info("Send a photo from {remote}".format(remote=remote_addr))

    try:
        if request.method == 'POST':
            keys = request.FILES.keys()
            if len(keys) == 1:
                # Get informations
                fileobj = request.FILES.get(keys[0])
                picture_name = fileobj.name
                datarel = keys[0][5:]
                if not re.match(r'^photo', keys[0]):
                    # Ensure the fieldname (minimal security - not really useful)
                    L.critical("ucomment.views.sendphoto: No field 'photo'. IP={0}".format(remote_addr))
                    return JsonResponse({'success': False, 'message': 'An error occured', 'datarel': datarel})

                # prepare names
                if not re.search(r'jpg|jpeg|png|gif', picture_name, re.I):
                    L.error("ucomment.views.sendphoto: Not allowed file format. Picture Name = {1} - IP={0}".format(remote_addr, picture_name))
                    return JsonResponse({'success': False, 'message': 'File type unauthorized', 'datarel': datarel})

                _name, ext = os.path.splitext(picture_name)
                dest_name = "%s%s" % (hashlib.sha1(request.user.username + str(time.time())).hexdigest(), ext)
                dest_dir = os.path.join(settings.MEDIA_ROOT, settings.BANDCOCHON_CONFIG.Upload.temp, dest_name)
                relative_path = '/'.join([settings.MEDIA_URL, settings.BANDCOCHON_CONFIG.Upload.temp, dest_name])
                relative_path = relative_path.replace('//', '/')

                # download picture
                file_upload = open(dest_dir, "wb+")
                for chunk in fileobj.chunks():
                    file_upload.write(chunk)
                file_upload.close()

                # Reduce it
                if ext.lower() != '.gif':
                    image = Image.open(dest_dir)
                    image.thumbnail((1024, 768), Image.ANTIALIAS)
                    image.save(dest_dir)

                # Send response
                L.info("ucomment.views.sendphoto: Everything goes fine. IP={0}".format(remote_addr))
                return JsonResponse({'success': True, 'image': relative_path, 'datarel': datarel})
        else:
            L.error('ucomment.views.sendphoto: Other method : {ip}'.format(ip=remote_addr))

    except Exception as e:
        L.error("ucomment.views.sendphoto: Error : {error} : {ip}".format(error=e, ip=remote_addr))

    return JsonResponse({'success': False, 'message': 'An error occured'})
