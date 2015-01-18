# -*- coding: utf-8 -*-

"""
Declare signals
"""

from django.core.signals import Signal

#
# The signal validate_comment is emitted before saving the content
# The receiver must returns a tuple. the first element must be
# a boolean. True on accept content, False otherwise. If the first
# tuple element is False, the second element must be a error
# message.
# The receiver fist argument is a HttpRequest object as sended by
# django and the second is the commentary content
#
validate_comment = Signal(providing_args=['request', 'content'])

#
# This signal is emited when a comment is saved
# The comment argument is a Django QuerySet object
#
comment_saved = Signal(providing_args=['comment'])


report_abuse = Signal(providing_args=['comment'])