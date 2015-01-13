# -*- coding: utf-8 -*-

"""
Declare signals
"""

from django.core.signals import Signal

# Used 
validate_comment = Signal(providing_args=['request', 'content'])
