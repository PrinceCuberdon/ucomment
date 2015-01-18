# -*- coding: UTF-8 -*-
# (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>

from django import template
from ucomment.models import Comment


register = template.Library()

@register.tag
def ucomment_get_for_uri(parser, token):
    tag_name, page_uri = token.split_contents()
    
    class UCommentGetForUriNode(template.Node):
        def render(self, context):
            uri = template.Variable(page_uri).resolve(context)
            context['ucomment_get_comments'] = Comment.objects.get_for_url(uri)
            return ''
        
    return UCommentGetForUriNode()

@register.tag
def ucomment_path(parser, token):
    """
    Install the page path into the submission form. The UComment context processor 
    Usage:
        add {% ucomment_path %} into the <form> tag
    """
    class UCommentPathNode(template.Node):
        def render(self, context):
            return '<input type="hidden" name="ucomment-path" value="{0}" />'.format(context['PAGE_URI'])

    return UCommentPathNode()

@register.tag
def ucomment_set_parent(parser, token):
    """
    Install a input form tag.
    Usage:
        add {% ucomment_set_parent comment %} where {{ comment }} is the parent comment
    """
    tag_name, comment_ctx = token.split_contents()
    
    class UCommentSetParentNode(template.Node):
        def render(self, context):
            comment = template.Variable(comment_ctx).resolve(context)
            return '<input type="hidden" name="ucomment-parent" value="{}" />'.format(comment.pk)
    
    return UCommentSetParentNode()
