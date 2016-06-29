# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(help_text=b'Internal site url for the comment', max_length=255, verbose_name=b'Internal URL', db_index=True)),
                ('content', models.TextField(verbose_name=b'Commentaire')),
                ('submission_date', models.DateTimeField()),
                ('external_user', models.CharField(max_length=40, null=True, blank=True)),
                ('moderate', models.BooleanField(default=False)),
                ('visible', models.BooleanField(default=False, db_index=True)),
                ('trash', models.BooleanField(default=False, db_index=True)),
                ('ip', models.GenericIPAddressField(null=True, blank=True)),
                ('is_message', models.BooleanField(default=False)),
                ('message_url', models.CharField(max_length=255, null=True, blank=True)),
                ('likeit', models.IntegerField(default=0)),
                ('dislikeit', models.IntegerField(default=0)),
                ('parent', models.ForeignKey(blank=True, to='ucomment.Comment', null=True)),
                ('user', models.ForeignKey(related_name='com_user', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-submission_date',),
            },
        ),
        migrations.CreateModel(
            name='CommentAbuse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comment', models.ForeignKey(to='ucomment.Comment')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CommentPref',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('only_registred', models.BooleanField(default=True, help_text='Only registred user can post (if no, every body can post)', verbose_name='Only registred')),
                ('use_like_dislike', models.BooleanField(default=True, help_text='Use the like and dislike system.', verbose_name='Use Like Dislike')),
                ('publish_on_submit', models.BooleanField(default=True)),
                ('register_ip', models.BooleanField(default=True, help_text='Save IP address on each post', verbose_name='Register IP')),
                ('abuse_max', models.SmallIntegerField(default=3, help_text='Maximum abuse count before moderation', verbose_name='Maximum abuse')),
                ('use_notification', models.BooleanField(default=False, help_text='Use notification inside the Wall', verbose_name=b'Notification')),
            ],
        ),
        migrations.CreateModel(
            name='LikeDislike',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('like', models.BooleanField(default=False, db_index=True)),
                ('dislike', models.BooleanField(default=False, db_index=True)),
                ('comment', models.ForeignKey(to='ucomment.Comment')),
                ('user', models.ForeignKey(related_name='ld_user', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
