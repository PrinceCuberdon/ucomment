# -*- coding: UTF-8 -*-
# ucomment is part of Band Cochon
# Band Cochon (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>

import json

# from PIL import Image

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import (HttpResponse, HttpResponseRedirect, Http404)
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.conf import settings
from django.views.generic import TemplateView

from django.contrib import messages

from .models import Comment, LikeDislike, CommentPref, CommentAbuse
from .signals import validate_comment, comment_saved, abuse_reported


class BookView(TemplateView):
    """
    The book view is called to display all messages from the url "/"
    """
    template_name = getattr(settings, "UCOMMENT_TEMPLATE", "ucomment/comments.html")

    def get_context_data(self, **kwargs):
        # Call the context
        context = super(BookView, self).get_context_data(**kwargs)
        context['book_comments'] = Comment.objects.get_for_url('/', 25)
        context['display_conn'] = True
        
        return context


# class BookViewNext(TemplateView):
#    template_name = getattr(settings, "UCOMMENT_TEMPLATE", "ucomment/comments.html")
#
#    def get(self, request, *args, **kwargs):
#        if not request.is_ajax() or not request.method == 'GET':
#            return HttpResponseBadRequest('')
#
#        count = int(request.GET.get('from', 0)) - 1
#        comments = list(Comment.objects.filter(visible=True, trash=False, url='/', parent=None)[count+1:count+25])
#        return render(request, {
#            'url': '/',
#            'book_comments': list(comments),
#            'display_conn': False
#        })

# def book_next(request):
#    """ Get next messages on the wall as JSON """
#    if request.is_ajax() and request.method == "GET":
#        count = int(request.GET.get('from', 0)) - 1
#        comments = list(Comment.objects.filter(visible=True, trash=False, url='/', parent=None)[count+1:count+25])
#        return render_to_response('inc/book.html', RequestContext(request, {
#            'url': '/',
#            'book_comments': list(comments),
#            'display_conn': False
#        }))
#
#    return HttpResponseBadRequest('')
#

def add(request):
    """ Post a message as AJAX """
    config = CommentPref.objects.get_preferences()
    if config.only_registred and not request.user.is_authenticated():
        if request.is_ajax():
            return HttpResponse(json.dumps({
                'success': False,
                'message': 'You must be authenticated in order to post'
            }), content_type="application/json")

        return HttpResponse("Error, you must be authenticated")

    if request.method == 'POST':
        if request.is_ajax():
            content = json.loads(request.body)
        else:
            content = request.POST.get('ucomment-content')

        site_name = 'http{0}://{1}'.format(
            's' if request.is_secure() else '',
            Site.objects.get_current().domain
        )
        
        referer = request.POST.get('ucomment-path', request.META['HTTP_REFERER'].replace(site_name, ''))

        if not content:
            if request.is_ajax():
                return HttpResponse(json.dumps({
                    'success': False,
                    'message': 'The content is empty'
                }), content_type="application/json")
            
            messages.add_message(request, messages.ERROR, "The content is empty")
            return HttpResponseRedirect(referer)
        
        # Emit the signal and catch result
        result = True
        sig_messages = []
        for f, r in validate_comment.send(sender=None, request=request, content=content):
            result &= r[0]
            if not r[0]:
                sig_messages.append(r[1])

        if result:
            if content:
                if request.is_ajax():
                    new_content = content['ucomment-content']
                    referer = content['path']
                else:
                    new_content = content

                comment = Comment.objects.create(
                    user=request.user,
                    url=referer,
                    content=new_content,
                    submission_date=timezone.now(),
                    visible=True,
                    ip=request.META['REMOTE_ADDR'],
                )
                comment_saved.send(sender=None, comment=comment)
                
                if request.is_ajax():
                    return HttpResponse(json.dumps({
                        'success': True,
                        'content': render_to_string('ucomment/single_comment.html', {
                            'comment': comment,
                            'user': request.user,
                            'ucomment_get_preferences': CommentPref.objects.get_preferences()
                        }),
                    }), content_type="application/json")

        else:
            if request.is_ajax():
                return HttpResponse(json.dumps({
                    'success': False,
                    'message': '\n'.join(sig_messages)
                }), content_type="application/json")

            for message in sig_messages:
                messages.add_message(request, messages.ERROR, message)
            
        return HttpResponseRedirect(referer)
    
    raise Http404("Bad Method")


@login_required
def like_dislike(request, comment_id, like=False, dislike=False):
    """
    Like or dislike a comment in both classical and AJAX way. In all cases, the
    user must be authenticated. In non-AJAX case the user is redirected where
    he comes from.
    """
    if request.method == 'GET' or request.method == 'PUT':
        comment = Comment.objects.filter(pk=comment_id)
        if comment.exists():
            comment = comment.get()
            if comment.user == request.user:
                if request.method == 'PUT':
                    return HttpResponse(
                        json.dumps({
                            'success': False,
                            'message': unicode(_("You can't vote for yourself"))
                        }),
                        content_type="application/json"
                    )
            else:
                # Ensure the user didn't vote yet. If not allow the vote
                if not LikeDislike.objects.filter(user=request.user, comment=comment).count():
                    LikeDislike.objects.create(like=like, dislike=dislike, user=request.user, comment=comment)
                else:
                    if request.method == 'PUT':
                        return HttpResponse(
                            json.dumps({
                                'success': False,
                                'message': unicode(_("You can't vote anymore for this message"))
                            }),
                            content_type="application/json"
                        )

        if request.method == 'PUT':
            return HttpResponse(json.dumps({
                'success': True,
                'pk': comment_id,
                'like': comment.likeit,
                'dislike': comment.dislikeit
            }), content_type="application/json")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    

@login_required
def report_abuse(request, comment_id):
    """
    Respond to a abuse report
    """
    comment = Comment.objects.get(pk=comment_id)

    # Ensure the user don't declare twice or more an abuse
    abuse = CommentAbuse.objects.filter(comment=comment, user=request.user)
    if abuse.exists():
        messages.add_message(request, messages.ERROR, _("You have already declared this comment as an abuse"))
    else:
        CommentAbuse.objects.create(comment=comment, user=request.user)
        comment.abuse_count += 1
        if comment.abuse_count >= CommentPref.objects.get_preferences().abuse_max:
            comment.visible = False
            comment.moderate = True
        comment.save()

        # Send a signal
        abuse_reported.send(sender=None, user=request.user, comment=comment)

    if request.is_ajax():
        return HttpResponse(json.dumps({
            'success': True
        }), content_type="application/json")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

#
# @login_required
# @csrf_exempt
# def sendphoto(request):
#    """ Send a picture, storeit into temp directory """
#    datarel = 0
#    try:
#        if request.method == 'POST':
#            is_html5 = True  # "HTTP_X_REQUESTED_WITH" in request.META
#            keys = request.FILES.keys()
#            if len(keys) == 1:
#                # Get informations
#                fileobj = request.FILES.get(keys[0])
#                picture_name = fileobj.name
#                datarel = keys[0][5:]
#                if not re.match(r'^photo', keys[0]):
#                    # Ensure the fieldname (minimal security - not really useful)
#                    if is_html5:
#                        return HttpResponse(json.dumps({
#                            'success':False,
#                            'message': 'An error occured',
#                            'datarel':datarel
#                        }), content_type="application/json")
#                    else:
#                        return HttpResponse("""<script type="text/javascript">window.top.window.imageUploaded""" +
#                                            """('Une erreur est survenue', 0, true);</script>""")
#
#                # prepare names
#                if not re.search(r'jpg|jpeg|png|gif', picture_name, re.I):
#                    if is_html5:
#                        return HttpResponse(json.dumps({
#                            'success':False,
#                            'message': 'File type unauthorized',
#                            'datarel': datarel
#                        }), content_type="application/json")
#                    else:
#                        return HttpResponse('''<script type="text/javascript">window.top.window.''' +
#                                            '''imageUploaded("Ce type de fichier n'est pas autoris&eacute;",''' +
#                                            '''%s, true);</script>''' % datarel)
#
#                _name, ext = os.path.splitext(picture_name)
#                dest_name = "%s%s" % (hashlib.sha1(request.user.username + str(time.time())).hexdigest(), ext)
#                dest_dir = os.path.join(settings.MEDIA_ROOT, settings.BANDCOCHON_CONFIG.Upload.temp, dest_name)
#                relative_path = '/'.join([settings.MEDIA_URL, settings.BANDCOCHON_CONFIG.Upload.temp, dest_name])
#                relative_path = relative_path.replace('//', '/')
#
#                # download picture
#                file_upload = open(dest_dir, "wb+")
#                for chunk in fileobj.chunks():
#                    file_upload.write(chunk)
#                file_upload.close()
#
#                # Reduce it
#                if ext.lower() != '.gif':
#                    image = Image.open(dest_dir)
#                    image.thumbnail((1024, 768), Image.ANTIALIAS)
#                    image.save(dest_dir)
#
#                # Send response
#                if is_html5:
#                    return HttpResponse(json.dumps({
#                        'success':True,
#                        'image': relative_path,
#                        'datarel': datarel
#                    }), content_type="application/json")
#                else:
#                    return HttpResponse("""<script type="text/javascript">window.top.window.imageUploaded""" +
#                                        """('%s', %s, false);</script>""" % (relative_path, datarel))
#        else:
#            ajax_log('ucomment.views.sendphoto: Get method : %s' % request.META['REMOTE_ADDR'])
#    except Exception as e:
#        ajax_log("ucomment.views.sendphoto: Error : %s : %s" % (e, request.META['REMOTE_ADDR']))
#
#    if is_html5:
#        return HttpResponse(json.dumps({
#            'success': False,
#            'message':'An error occured'
#        }), content_type="application/json")
#    else:
#        return HttpResponse("""<script type="text/javascript">window.top.window.imageUploaded""" +
#                            """('Une erreur est survenue et tout a merdu', %s, true);</script>""" % datarel)
