# -*- coding: utf-8 -*-

import locale


def convert_date(value):
    """ replace month because strftime is not unicode compliant """
    return value.strftime("%d %B %Y").decode(locale.getpreferredencoding())
