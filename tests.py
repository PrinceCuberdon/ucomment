# -*- coding: utf-8 -*-
"""
Test file for the UComment Framework
"""

from unittest import TestCase
import datetime
import locale
import platform

from django.db.models import QuerySet

from .models import convert_date, CommentPref


class ConvertDateTest(TestCase):
    def setUp(self):
        """ Set a locale into french locale. August contains a
        unicode character in french. but as MS Windows use a different key
        for Country/Region code we must test first on which platform we are """
        if platform.system() == "Windows":
            locale.setlocale(locale.LC_ALL, "fra_fra")
        else:
            locale.setlocale(locale.LC_ALL, locale.locale_alias['fr_fr.utf8@euro'])

    def test_convert_date(self):
        """
        An exception (UnicodeDecodeError) must not be raised
        """
        dt = datetime.datetime(2014, 8, 1)
        with self.assertRaises(Exception):
            try:
                convert_date(dt)
            except:
                pass
            else:
                raise Exception


class CommentPrefManagerTest(TestCase):
    def test_get_default_preferences(self):
        """ If an instance don't exists it must be created """
        pref = CommentPref.objects.get_preferences()

        self.assertIsNotNone(pref, "The preferences exists")
        self.assertNotIsInstance(pref, QuerySet, "This is not a QuerySet")
        self.assertIsInstance(pref, CommentPref, "The preferences is correct instance")

        # Ensure default
        self.assertTrue(pref.only_registred)
        self.assertTrue(pref.use_like_dislike)
        self.assertTrue(pref.publish_on_submit)
        self.assertTrue(pref.register_ip)
        self.assertTrue(pref.abuse_max, 3)
        self.assertFalse(pref.use_notification)
