# -*- coding: utf-8 -*-
"""
Test file for the UComment Framework
"""

from unittest import TestCase
import datetime
import platform

from django.utils import timezone

import locale
from django.db.models import QuerySet

from .models import convert_date, CommentPref, Comment
import api

comments = [{
    'url': '/an/url',
    'content': 'a content 1 motatrouver',
    'submission_date': timezone.now(),
    'visible': True
}, {
    'url': '/an/url',
    'content': 'a content 2 motatrouver ',
    'submission_date': timezone.now()
}, {
    'url': '/an/url',
    'content': 'a content 6',
    'submission_date': timezone.now(),
    'visible': True
}, {
    'url': '/an/url/2',
    'content': 'a content 3',
    'submission_date': timezone.now()
}, {
    'url': '/an/url/2',
    'content': 'a content 4 autremot',
    'submission_date': timezone.now(),
    'visible': True
}, {
    'url': '/an/url/3',
    'content': 'a content autremot 7',
    'submission_date': timezone.now()
}, {
    'url': '/an/url/3',
    'content': 'a content 8',
    'submission_date': timezone.now()
}, {
    'url': '/an/url/3',
    'content': 'a content 9',
    'submission_date': timezone.now()
}, {
    'url': '/an/url/3',
    'content': 'a content 10 autremot',
    'submission_date': timezone.now(),
    'visible': True
}]


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
                raise Exception()


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


class CommentAPITest(TestCase):
    def setUp(self):
        for entry in comments:
            Comment.objects.create(
                url=entry['url'],
                content=entry['content'],
                submission_date=entry['submission_date'],
                visible=entry['visible'] if 'visible' in entry else False
            )

    def tearDown(self):
        Comment.objects.all().delete()

    def test_get_count(self):
        self.assertEqual(api.get_count("/an/url"), 2)
        self.assertEqual(api.get_count("/"), 0)

    def test_get_comments(self):
        self.assertEqual(len(api.get_comments("/an/url")), 2)
        self.assertEqual(len(api.get_comments("/an/url", 1)), 1)

    def test_search_words(self):
        self.assertEqual(len(api.search_words(["motatrouver"])), 1) # Single word
        self.assertEqual(len(api.search_words(["content", "autremot"])), 2)  # AND words
