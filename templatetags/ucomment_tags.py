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
