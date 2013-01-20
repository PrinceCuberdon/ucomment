# -*- coding: UTF-8 -*-
# ucomment is part of Band Cochon
# Band Cochon (c) Prince Cuberdon 2011 and Later <princecuberdon@bandcochon.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import datetime
import re
import json
import os

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponse

from ucomment.templatetags.ucomment_tags import comment_count, get_total_comments_count
from ucomment.models import CommentPref, Comment, LikeDislike
from bandcochon.models import Utilisateur

SMILIES = (
    ('O:)',     'angel'),
    ('O:-)',    'angel'),
    (':p',      'raspberry'),
    (':-p',     'raspberry'),
    (';)',      'wink'),
    (';-)',     'wink'),
    ('>:)',     'devilish'),
    ('>:-)',    'devilish'),
    (']:-)',    'devilish'),
    (']:)',     'devilish'),
    ('8|',      'cool'),
    ('8-|',     'cool'),
    ('B)',      'cool'),
    ('B-)',     'cool'),
    (":'-(",    'crying'),
    (":'(",     'crying'),
    (':$',      'embarrassed'),
    ('8)',      'glasses'),
    ('8-)',     'glasses'),
    (':*',      'kiss'),
    (':-*',     'kiss'),
    (':D',      'laugh'),
    (':-D',     'laugh'),
    (':-|',     'uncertain'),
    (':|',      'uncertain'),
    (':(',      'sad'),
    (':-(',     'sad'),
    ('+o(',     'sick'),
    (':o',      'surprise'),
    (':O|',     'surprise'),
    (':0|',     'surprise'),
    ('o_O',     'surprise'),
    (':-o',     'surprise'),
    (':-O',     'surprise'),
    ('v.v',     'tired'),
    (':~',      'worried'),
    (':-~',     'worried'),
    (':\\',     'smirk'),
    (':-\\',    'smirk'),
    (':)',      'smile'),
    (':-)',     'smile'),
    (':]',      'smile-big'),
    (':-]',     'smile-big'),
    ('[ninja]', 'ninja'),
    (':@',      'angry'),
    (':-@',     'angry'),
    ('[monkey]','monkey'),
    ('O.o',     'pig'),
)

# All kind of youtube links
YOUTUBE_LINKS = (
    "http://www.youtube.com/watch?v=21o-M_VKmo0",                           # Normal link
    'http://youtu.be/21o-M_VKmo0',                                          # Short link
    'http://www.youtube.com/watch?feature=endscreen&NR=1&v=21o-M_VKmo0',
    'http://www.youtube.com/watch?v=21o-M_VKmo0&feature=relmfu',
    #'http://www.youtube.com/watch?feature=player_embedded&v=sdci4CUJxPU',  # This one fail
)
YOUTUBE_VIDEO_CODE = '<iframe width="560" height="315" src="http://www.youtube.com/embed/21o-M_VKmo0" frameborder="0" allowfullscreen></iframe>'

# All kind of dailymotion links
# If you speak or understand french, this video is hilarious :')
DAILYMOTION_LINKS = (
    'http://www.dailymotion.com/video/x80385_europa-corp-la-recette-luc-besson-p_fun?search_algo=2',
    'http://www.dailymotion.com/video/x80385_europa-corp-la-recette-luc-besson-p_fun',
    'http://www.dailymotion.com/video/x80385_europa-corp-la-recette-luc-besson-p_fun?ralg=meta2-only#from=playrelon-1'
)
DAILYMOTION_VIDEO_CODE = '<iframe frameborder="0" width="560" height="315" src="http://www.dailymotion.com/embed/video/x80385"></iframe><br>'

# These are tests for outhosted pictures
IMAGES = (
    ('http://mypicture.png', '<img src="http://mypicture.png" style="max-width:500px" /><br class="clear" />'),
    ('http://mypicture.jpg', '<img src="http://mypicture.jpg" style="max-width:500px" /><br class="clear" />'),
    ('http://mypicture.gif', '<img src="http://mypicture.gif" style="max-width:500px" /><br class="clear" />'),
)

class TagsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="fake-test-user", # Are we sure that nobody will use this username ?
            email="fake@nowhere.tld"
        )
        
    def test_comment_count(self):
        """ Count messages on the main wall (url == /) """
        self.assertIsInstance(comment_count('/'), int)
    
    def test_total_comments_count(self):
        """ Count all comments for a user (the last one). Must be an int > 0 """
        # Caution MySQL count return a long and SQLite 3 an int. Test are made on SQLite3
        self.assertIsInstance(get_total_comments_count(self.user), int) 
        self.assertGreaterEqual(get_total_comments_count(self.user), 0)
        
class Modeltest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="fake-test-user", # Are we sure that nobody will use this username ?
            email="fake@nowhere.tld"
        )
        self.superuser = User.objects.create_superuser("iam-superuser-man", "superuser@nowhere.tld", "you-should-test")
        
        # defaults contants
        self.only_registred = True
        self.use_like_dislike = True
        self.publish_on_submit = True
        self.register_ip = True
        self.abuse_max = 3
        self.use_notification = False
        
        # Create a pref
        self.pref = CommentPref.objects.create()
        
    def __create_comment(self, content, parent=None, url="/", user=None):
        """ Private : Create a comment with the given content """
        if user is None:
            user = self.user
            
        return Comment.objects.create(
                url=url,
                content=content,
                parent=parent,
                user=user,
                submission_date=datetime.datetime.now(),
                visible=True
            )

    def test_comment_pref(self):
        """ Test default pref """
        self.assertIsInstance(self.pref, CommentPref)
        self.assertEqual(self.pref.only_registred,      self.only_registred)
        self.assertEqual(self.pref.use_like_dislike,    self.use_like_dislike)
        self.assertEqual(self.pref.publish_on_submit,   self.publish_on_submit)
        self.assertEqual(self.pref.register_ip,         self.register_ip)
        self.assertEqual(self.pref.abuse_max,           self.abuse_max)
        self.assertEqual(self.pref.use_notification,    self.use_notification)
        
    def test_smilies(self):
        """ Test if smilies are correctly converted. """
        for smiley in SMILIES:
            comment = self.__create_comment('This is a test with a smiley %s' % smiley[0])
            self.assertGreaterEqual(comment.content.find('<span class="icon inline-icon smiley-%s"></span>' % smiley[1]), 0)
            comment.delete()
            
    def test_youtube(self):
        """ Test youtube  url convertion """
        for url in YOUTUBE_LINKS:
            comment = self.__create_comment('This is a post with youtube link : %s' % url)
            self.assertGreaterEqual(comment.content.find(YOUTUBE_VIDEO_CODE), 0, url)
            comment.delete()
        
    def test_dailymotion(self):
        """ Test dailymotion url convertion """
        for url in DAILYMOTION_LINKS:
            comment = self.__create_comment('This is a post with dailymotion link : %s' % url)
            self.assertGreaterEqual(comment.content.find(DAILYMOTION_VIDEO_CODE), 0, url)
            comment.delete()
            
    def test_images(self):
        """ Test images insertion in comment """
        for img in IMAGES:
            comment = self.__create_comment('test image : %s' % img[0])
            self.assertGreaterEqual(comment.content.find(img[1]), 0)
            comment.delete()
            
    def test_links(self):
        """ test link convertion """
        comment = self.__create_comment('Test link : http://www.bandcochon.re/')
        self.assertGreaterEqual(comment.content.find('<a href="http://www.bandcochon.re/" target="_blank">http://www.bandcochon.re/</a>'), 0)
        comment.delete()

    def test_no_link(self):
        """ Test link convertionless """
        comment = self.__create_comment('Test link : <a href="http://www.bandcochon.re/" target="_blank">http://www.bandcochon.re/</a>')
        self.assertGreaterEqual(len(re.findall(r'href', comment.content)), 1)
        comment.delete()
        
    def test_clear_trash(self):
        """ Test trash unvisible comment """
        comment = self.__create_comment('This is a test')
        comment.trash = True
        comment.save()
        self.assertEqual(Comment.objects.filter(trash=True).count(), 1)
        comment.admin_clear_trash()
        self.assertEqual(Comment.objects.filter(trash=True).count(), 0)
        self.assertEqual(Comment.objects.all().count(), 0)
        
    def test_comment_heritage(self):
        """ test a response to a comment """
        comment1 = self.__create_comment('this is a message')
        comment2 = self.__create_comment('This is another message', parent=comment1)
        self.assertEqual(comment2.parent, comment1)
        
    #
    # Test model methods ######################################################
    #
    def test_absolute_url(self):
        firsturl = '/test/message/'
        scndurl = '/another/test/message/'
        
        # Parent message
        comment1 = self.__create_comment('This is a message',url=firsturl)
        self.assertEqual(comment1.url, firsturl)
        
        # Son message
        comment2 = self.__create_comment('This is another message with a parent', parent=comment1, url=scndurl)
        self.assertEqual(comment1.url, comment2.get_absolute_url())
        
        # Done
        comment1.delete()
        comment2.delete()
        
    def test_get_response(self):
        """ Test response message """
        comment1 = self.__create_comment("This is a message")
        comment2 = self.__create_comment('This is another message', parent=comment1)
        comment3 = self.__create_comment('this is again another message', parent=comment1)
        
        self.assertIsInstance(comment1.get_response(), list)
        self.assertEqual(comment2.parent, comment1)
        self.assertEqual(comment3.parent, comment1)
        self.assertEqual(len(comment1.get_response()), 2)
        comment3.visible=False
        comment3.save()
        self.assertEqual(len(comment1.get_response()), 1)
        
        comment1.delete()
        comment2.delete()
        comment3.delete()
        
    def test_can_set_abuse(self):
        """ test can set abuse """
        comment = self.__create_comment("This is a message")

        self.assertEqual(comment.can_set_abuse(self.user), True)
        comment.set_abuse(self.user)
        
        self.assertEqual(comment.can_set_abuse(self.user), False)
        self.assertEqual(comment.can_set_abuse(self.superuser), True)
        comment.delete()
        
    def test_abuse_count(self):
        """ Test comments abusement  """
        comment = self.__create_comment("This is a message")
        self.assertEqual(comment.get_abuse_count(), 0)
        
        comment.set_abuse(self.user)
        self.assertEqual(comment.get_abuse_count(), 1)
        
        comment.delete()
                
    def test_comment_like_dislike(self):
        comment = self.__create_comment("This is a message", user=self.superuser)
        self.assertEqual(len(comment.get_agreeiers()), 0)
        self.assertEqual(len(comment.get_disagreeiers()), 0)
        
        like = LikeDislike.objects.create(comment=comment, like=True, dislike=False, user=self.user)
        self.assertIsInstance(comment.get_agreeiers(), list)
        self.assertIsInstance(comment.get_disagreeiers(), list)
        self.assertEqual(len(comment.get_agreeiers()), 1)
        self.assertEqual(len(comment.get_disagreeiers()), 0)
        like.delete()
        
        dislike = LikeDislike.objects.create(comment=comment, like=False, dislike=True, user=self.user)
        self.assertIsInstance(comment.get_agreeiers(), list)
        self.assertIsInstance(comment.get_disagreeiers(), list)
        self.assertEqual(len(comment.get_agreeiers()), 0)
        self.assertEqual(len(comment.get_disagreeiers()), 1)
        dislike.delete()
        
        comment.delete()
        
    def test_serialization(self):
        # Create a fake Utilisateur
        utilisateur = Utilisateur.objects.create(user=self.user)
        comment = self.__create_comment("This is a message")
        self.assertIsInstance(Comment.objects.serialize("/"), list)
        self.assertEqual(len(Comment.objects.serialize('/')), 1)
        self.assertEqual(len(Comment.objects.serialize('/nothing-here/')), 0)
    
        # Is JSONisable ?
        self.assertIsInstance(json.dumps(Comment.objects.serialize('/'), ensure_ascii=False), unicode)
        utilisateur.delete()
        comment.delete()
        
class ViewsTest(TestCase):
    def setUp(self):
        """ Create two user and a comment """
        self.user1 = User.objects.create_user(username="fake-test-user1",
                                              email="fake1@nowhere.tld", 
                                              password="fake-test-password")
        self.utili1 = Utilisateur.objects.create(user=self.user1)
        
        self.user2 = User.objects.create_user(username="fake-test-user2",
                                              email="fake2@nowhere.tld", 
                                              password="fake-test-password")
        self.utili2 = Utilisateur.objects.create(user=self.user2)
        
    def test_postmessage(self):
        """ To pass this test, the post message must posted by a registred user, in ajax mode and with as message content
        Todo : This was my first Test procedure of my life ! :) Explode the test procedure """
        client = Client()
        #
        # In POST mode -- No AJAX -- Not authenticated -- MUST FAIL **********
        #
        # Normal
        response = client.post(reverse('ucomment_postmessage'), {'content':'this is a message' })
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(Comment.objects.all().count(), 0)
        
        # Without nothing
        response = client.post(reverse('ucomment_postmessage'))
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(Comment.objects.all().count(), 0)

        # Without content
        response = client.post(reverse('ucomment_postmessage'), { 'parent':None})
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(Comment.objects.all().count(), 0)
        
        #
        # In post mode -- no ajax -- authenticated -- must fail ***************
        #
        # Login
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        
        # Normal post
        response = client.post(reverse('ucomment_postmessage'), {'parent':None, 'content':'this is a message' })
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(Comment.objects.all().count(), 0)
        
        # Without nothing
        response = client.post(reverse('ucomment_postmessage'))
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(Comment.objects.all().count(), 0)

        # Without content
        response = client.post(reverse('ucomment_postmessage'), { 'parent':None})
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(Comment.objects.all().count(), 0)
        
        client.logout()
        
        #
        # In POST and AJAX -- User is not authenticated -- Must fail **********
        #
        response = client.post(reverse('ucomment_postmessage'), {'parent': None, 'content':'this is a message' },
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(Comment.objects.all().count(), 0)
        
        # Without nothing
        response = client.post(reverse('ucomment_postmessage'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(Comment.objects.all().count(), 0)

        # Without content
        response = client.post(reverse('ucomment_postmessage'), { 'parent':None}, 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(Comment.objects.all().count(), 0)
        
        #
        # In POST and AJAX -- User is authenticated ***************************
        #
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        
        # Normal post -- Must Success
        response = client.post(reverse('ucomment_postmessage'), {'content':'this is a message' }, 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        self.assertIsInstance(json.loads(response.content), dict)
        self.assertEqual(Comment.objects.all().count(), 1)
        
        # Without nothing -- Nothing - Fail
        response = client.post(reverse('ucomment_postmessage'),HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(Comment.objects.all().count(), 1)

        # Without content - Fail 
        response = client.post(reverse('ucomment_postmessage'), {},HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(Comment.objects.all().count(), 1)
        
        # Post a response
        theMessage = u'This is another message'
        parent = Comment.objects.latest('id')
        response = client.post(reverse('ucomment_postmessage'), {'content':theMessage,'parent':parent.id} , 
                               HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        content = json.loads(response.content)
        self.assertIsInstance(content, dict)
        self.assertEqual(content['content'].strip(), theMessage)
        self.assertEqual(Comment.objects.all().count(), 2)
        self.assertEqual(len(parent.get_response()), 1)
        
        
    def test_agree_not_connected_no_data(self):
        """ to pass this test the must must agree another user message, be registred """
        client = Client()
        
        # Not connected and POST !AJAX return  a bad request
        response = client.post(reverse('ucomment_agree'))
        self.assertIsInstance(response, HttpResponseBadRequest)
        
        # Not connected, POST AJAX -> return a json script with success=false
        response = client.post(reverse('ucomment_agree'), {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIsInstance(response, HttpResponse)
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        content = json.loads(response.content)
        self.assertFalse(content['success'])
        self.assertIsInstance(content['message'], unicode)
        
    def test_agree_connected_not_ajax(self):
        client = Client()
        # Connect
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        
        # Connected  POST !AJAX -> return a bad request
        response = client.post(reverse('ucomment_agree'), {'message': 1})
        self.assertIsInstance(response, HttpResponseBadRequest)
        
    def test_agree_no_data(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        
        # Connected POST AJAX No QueryDict -> bad request
        response = client.post(reverse('ucomment_agree'), {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIsInstance(response, HttpResponseBadRequest)

    def test_agree_non_existing_data(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        

        # Connect POST AJAX non existing comment id -> bad request
        response = client.post(reverse('ucomment_agree'), {'message': 999}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIsInstance(response, HttpResponse)
        self.assertIsInstance(response, HttpResponseBadRequest)

    def test_agree_all_good(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        
        # Post a message to have an id
        response = client.post(reverse('ucomment_postmessage'), {'content':'this is a message' }, 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        content = json.loads(response.content)
        self.assertIsInstance(content, dict)
        self.assertTrue(content.has_key('commentid'))
        commentid = content['commentid']
        self.assertIsInstance(commentid, int) # MySQL should return a long
        
        # Connected POST AJAX but our message can't vote for ourself -> return a json with success = false
        response = client.post(reverse('ucomment_agree'), { 'message': commentid }, 
                               HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        self.assertIsInstance(response, HttpResponse)
        content = json.loads(response.content)
        self.assertIsInstance(content, dict)
        self.assertTrue(content.has_key('success'))
        self.assertTrue(content.has_key('message'))
        self.assertIsInstance(content['message'], unicode)
        self.assertFalse(content['success'])
        
        # 
        anotherClient = Client()
        success = anotherClient.login(username="fake-test-user2", password="fake-test-password")
        self.assertTrue(success)
        response = anotherClient.post(reverse('ucomment_agree'), 
                                      { 'message': commentid } , 
                                      HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        self.assertIsInstance(response, HttpResponse)
        content = json.loads(response.content)
        self.assertIsInstance(content, dict)
        self.assertTrue(content.has_key('success'))
        self.assertTrue(content['success'])
        self.assertTrue(content.has_key('message'))
        self.assertTrue(content['success'])
        self.assertIsInstance(content['message'], unicode)
        self.assertTrue(content.has_key('agreeiers'))
        self.assertIsInstance(content['agreeiers'], list)
        self.assertGreater(len(content['agreeiers']), 0)
        
        # Can't vote twice
        response = anotherClient.post(reverse('ucomment_agree'), { 'message': commentid}, 
                                      HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        self.assertIsInstance(response, HttpResponse)
        content = json.loads(response.content)
        self.assertIsInstance(content, dict)
        self.assertTrue(content.has_key('success'))
        self.assertTrue(content.has_key('message'))
        self.assertFalse(content['success'])
        self.assertIsInstance(content['message'], unicode)
        
        
    def test_disagree_not_connected_no_data_no_ajax(self):
        """ to pass this test the must must disagree another user message, be registred """
        client = Client()
        
        # Not connected and POST !AJAX return  a bad request
        response = client.post(reverse('ucomment_disagree'))
        self.assertIsInstance(response, HttpResponseBadRequest)
        
    def test_disagree_not_connected_no_data(self):
        """ Not connected, POST AJAX -> return a json script with success=false """
        client = Client()
        response = client.post(reverse('ucomment_disagree'), {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIsInstance(response, HttpResponse)
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        content = json.loads(response.content)
        self.assertFalse(content['success'])
        self.assertIsInstance(content['message'], unicode)
        
        # Connect
    def test_disagree_connected_no_ajax(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        
        # Connected  POST !AJAX -> return a bad request
        response = client.post(reverse('ucomment_disagree'), {'message': 1})
        self.assertIsInstance(response, HttpResponseBadRequest)
        
    def test_disagree_connected_ajax(self):
        # Connected POST AJAX No QueryDict -> bad request
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        response = client.post(reverse('ucomment_disagree'), {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIsInstance(response, HttpResponseBadRequest)

    def test_disagree_non_existing_id(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)

        # Connect POST AJAX non existing comment id -> bad request
        response = client.post(reverse('ucomment_disagree'), {'message': 999}, 
                               HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIsInstance(response, HttpResponse)
        self.assertIsInstance(response, HttpResponseBadRequest)

    def test_disagree_cant_vote_for_me(self):
        # Post a message to have an id
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        response = client.post(reverse('ucomment_postmessage'), {'content':'this is a message' }, 
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        content = json.loads(response.content)
        self.assertIsInstance(content, dict)
        self.assertTrue(content.has_key('commentid'))
        commentid = content['commentid']
        self.assertIsInstance(commentid, int) # MySQL returns a long
        
        # Connected POST AJAX but our message can't vote for ourself -> return a json with success = false
        response = client.post(reverse('ucomment_disagree'), { 'message': commentid }, 
                               HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        self.assertIsInstance(response, HttpResponse)
        content = json.loads(response.content)
        self.assertIsInstance(content, dict)
        self.assertTrue(content.has_key('success'))
        self.assertTrue(content.has_key('message'))
        self.assertIsInstance(content['message'], unicode)
        self.assertFalse(content['success'])
        
        anotherClient = Client()
        success = anotherClient.login(username="fake-test-user2", password="fake-test-password")
        self.assertTrue(success)
        response = anotherClient.post(reverse('ucomment_disagree'), 
                                      { 'message': commentid } , 
                                      HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        self.assertIsInstance(response, HttpResponse)
        content = json.loads(response.content)
        self.assertIsInstance(content, dict)
        self.assertTrue(content.has_key('success'))
        self.assertTrue(content['success'])
        self.assertTrue(content.has_key('message'))
        self.assertTrue(content['success'])
        self.assertIsInstance(content['message'], unicode)
        self.assertTrue(content.has_key('disagreeiers'))
        self.assertIsInstance(content['disagreeiers'], list)
        self.assertGreater(len(content['disagreeiers']), 0)

        # Can't vote twice
        response = anotherClient.post(reverse('ucomment_disagree'), 
                                      { 'message': commentid }, 
                                      HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        self.assertIsInstance(response, HttpResponse)
        content = json.loads(response.content)
        self.assertIsInstance(content, dict)
        self.assertTrue(content.has_key('success'))
        self.assertTrue(content.has_key('message'))
        self.assertFalse(content['success'])
        self.assertIsInstance(content['message'], unicode)
        
    #
    # Comment Moderation ######################################################
    #
    def test_moderate_noconnected_noajax_nocontent(self):
        """ The user must be registred, he should signal once per picture the abuse, Stuff remove immediatly the comment  """
        client = Client()
        
        # Not logged no id, no ajax -> Redirect to login page
        response = client.post(reverse('ucomment_moderate'), follow=True)
        self.assertGreaterEqual(response.redirect_chain[0][0].find(reverse('account_home')), 0)
        
    def test_moderate_connected_noajax_nocontent(self):
        """ User connected, no ajax, no comment id given """
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        response = client.post(reverse('ucomment_moderate'))
        self.assertIsInstance(response, HttpResponseBadRequest)
        
    def test_moderate_connected_ajax_nocontent(self):
        """ User is connected, ajax mlode, no comment """
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        response = client.post(reverse('ucomment_moderate'), {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIsInstance(response, HttpResponseBadRequest)
        
    def test_moderate_connected_ajax_content_dontexists(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        response = client.post(reverse('ucomment_moderate'), {'rel':1}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIsInstance(response, HttpResponseBadRequest)
        
    def test_moderate_connected_ajax_content_exists(self):
        client = Client()
        comment = Comment.objects.create(user=self.user1, 
                                         url="/", 
                                         content="This is a message", 
                                         submission_date=datetime.datetime.now())
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        response = client.post(reverse('ucomment_moderate'), {'rel': comment.id}, 
                               HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertIsInstance(response, HttpResponse)
        self.assertNotIsInstance(response, HttpResponseBadRequest)
        
    def test_moderate_connect_noajax_content_exists(self):
        client = Client()
        comment = Comment.objects.create(user=self.user1, 
                                         url="/", 
                                         content="This is a message", 
                                         submission_date=datetime.datetime.now())
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        response = client.post(reverse('ucomment_moderate'), {'rel': comment.id})
        self.assertIsInstance(response, HttpResponseBadRequest)
        
        
    def test_next_comments(self):
        """ Don't know how to do that """
        
    def test_show_last(self):
        """ Don't know how to do that """
        
    #
    # Send_photo ##############################################################
    # The tested file must exists and it is static/images/favicon.png #########
    #
    filename_png = 'test_bc/resources/testpicture.png'
    filename_gif = 'test_bc/resources/testpicture.gif'
    filename_jpg = 'test_bc/resources/testpicture.jpg'
    filename_jpeg = 'test_bc/resources/testpicture.jpeg'
    fakename = "site_media/temp/fake.nothing"
    
    def test_send_photo_noconnect(self):
        client = Client()
        response = client.post(reverse('ucomment_sendphoto'), follow=True)
        self.assertGreaterEqual(response.redirect_chain[0][0].find(reverse('account_home')), 0)
        
    def test_send_photo_connect_get(self):
        """ Test the get method. We take care on translation """
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        response = client.get(reverse('ucomment_sendphoto'))
        self.assertIsInstance(response,HttpResponse)
        self.assertRegexpMatches(response.content, r'''\<script type="text/javascript"\>window\.top\.window\.imageUploaded\('.*?', 0, true\);\</script\>''')
        
    def test_send_photo_connect_nomultipart(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        with open(self.filename_png,"r") as fp:
            response = client.post(reverse('ucomment_sendphoto'), {'photo0' : fp }, CONTENT_TYPE="")
            self.assertRegexpMatches(response.content, r'''\<script type="text/javascript"\>window\.top\.window\.imageUploaded\('.*?', 0, true\);\</script\>''')
    
    def test_send_photo_connect_multipart_wrongname(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        with open(self.filename_png,"r") as fp:
            response = client.post(reverse('ucomment_sendphoto'), {'abcde0' : fp })
            self.assertRegexpMatches(response.content, r'''\<script type="text/javascript"\>window\.top\.window\.imageUploaded\('.*?', 0, true\);\</script\>''')
            self.__cleanupTemp()
    
    def test_send_photo_connect_multipart_goodname_wrongformat(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        
        with open(self.filename_png, "rb") as fb:
            open(self.fakename, 'wb').write(fb.read())
            
        self.assertTrue(os.path.exists(self.fakename))

                
        with open(self.fakename, "r") as fp:
            response = client.post(reverse('ucomment_sendphoto'), {'photo0': fp})
            self.assertRegexpMatches(response.content, r'''\<script type="text/javascript"\>window\.top\.window\.imageUploaded\(".*?", 0, true\);\</script\>''')
            self.__cleanupTemp()
    
        
    def test_send_photo_connect_multipart_goodname_goodformat_png(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        with open(self.filename_png,"r") as fp:
            response = client.post(reverse('ucomment_sendphoto'), {'photo0': fp})
            self.assertRegexpMatches(response.content, r"""\<script type="text/javascript"\>window\.top\.window\.imageUploaded\('.*?', \d+, false\);</script>""")
            self.__cleanupTemp()
        
    def test_send_photo_connect_multipart_goodname_goodformat_gif(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        with open(self.filename_gif,"r") as fp:
            response = client.post(reverse('ucomment_sendphoto'), {'photo0': fp})
            self.assertRegexpMatches(response.content, r"""\<script type="text/javascript"\>window\.top\.window\.imageUploaded\('.*?', \d+, false\);</script>""")
            self.__cleanupTemp()

    def test_send_photo_connect_multipart_goodname_goodformat_jpg(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        with open(self.filename_jpg,"r") as fp:
            response = client.post(reverse('ucomment_sendphoto'), {'photo0': fp})
            self.assertRegexpMatches(response.content, r"""\<script type="text/javascript"\>window\.top\.window\.imageUploaded\('.*?', \d+, false\);</script>""")
            self.__cleanupTemp()

    def test_send_photo_connect_multipart_goodname_goodformat_jpeg(self):
        client = Client()
        success = client.login(username="fake-test-user1", password="fake-test-password")
        self.assertTrue(success)
        with open(self.filename_jpeg,"r") as fp:
            response = client.post(reverse('ucomment_sendphoto'), {'photo0': fp})
            self.assertRegexpMatches(response.content, r"""\<script type="text/javascript"\>window\.top\.window\.imageUploaded\('.*?', \d+, false\);</script>""")
            self.__cleanupTemp()

    def __cleanupTemp(self):
        for f in os.listdir('site_media/temp/'):
            os.remove(os.path.join('site_media/temp', f))
        