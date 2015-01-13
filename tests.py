# -*- coding: utf-8 -*-

from unittest import TestCase
from django.utils import timezone
import locale
import platform

from django.test import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from .models import convert_date, CommentPref, Comment

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
        self.assertIsNotNone(pref)        
        self.assertIsInstance(pref, CommentPref)
        
        
class ContextProcessorTest(TestCase):
    def test_page_uri(self):
        c = Client()
        result = c.get('/')
        self.assertIn('PAGE_URI', result.context)
        self.assertEqual(result.context['PAGE_URI'], '/')
        

class LikeDislikeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', email='test@test.fr', password='test')
        Comment.objects.create(
            url='/',
            content="This is a message",
            user=self.user,
            submission_date=timezone.now()
        )
        
    def tearDown(self):
        self.user.delete()
        
    def test_cant_likedislike_non_existing_comment(self):
        client = Client()
        client.get(reverse('ucomment_like_it', args=(100,)))
        
    def test_must_be_logged(self):
        client = Client()
        client.get(reverse('ucomment_like_it', args=(1,)))
    
    def test_like(self):
        pass
    
    def test_dontlike(self):
        pass
    
    def test_like_ajax(self):
        pass
    
    def test_dontlike_ajax(self):
        pass
    

