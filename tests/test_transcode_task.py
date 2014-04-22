# -*- coding: utf-8 -*-

# Base Application of the CloudNcode SaaS Transcoding Platform
# Retrieved from https://bitbucket.org/cloudncode/cloudncode.git
u"""
    Test the transcode task of the CloudNcode base application.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 CloudNcode Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import errno, json, logging.config, mock, os, shutil
from codecs import open
from os.path import basename, dirname, exists, join
from nose.tools import ok_
from pytoolbox.filesystem import try_makedirs, try_remove
from pytoolbox.network.http import download
from pytoolbox.subprocess import rsync

from encodebox.lib import generate_unguessable_filename

from .settings import (
    set_test_settings, MEDIA_INPUTS_DIRECTORY, MEDIA_REMOTE_DIRECTORY, LOCAL_DIRECTORY, REMOTE_DIRECTORY, SETTINGS,
    SETTINGS_FILENAME
)


class TestTranscodeTasks(object):

    def setUp(self):
        set_test_settings()
        for directory in (LOCAL_DIRECTORY, REMOTE_DIRECTORY):
            try_makedirs(directory)

        logging.config.dictConfig({
            'version': 1,
            'disable_existing_loggers': True,
            'formatters': {'simple': {'format': '%(levelname)s %(message)s'}},
            'handlers': {'console': {'level': 'DEBUG', 'class': 'logging.StreamHandler', 'formatter': 'simple'}},
            'loggers': {'encodebox.tasks.transcode': {'handlers': ['console'], 'propagate': True, 'level': 'DEBUG'}}
        })

    def tearDown(self):
        try_remove(SETTINGS_FILENAME)
        shutil.rmtree(LOCAL_DIRECTORY)
        shutil.rmtree(REMOTE_DIRECTORY)

    def is_empty(self, directory):
        try:
            return len(os.listdir(directory)) == 0
        except OSError as e:
            if e.errno == errno.ENOENT:
                return True
            return False

    def test_transcode_text(self):
        with mock.patch('encodebox.celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
            from encodebox import tasks
            in_relpath = '1/1/uploaded/test.txt'
            in_abspath = join(LOCAL_DIRECTORY, in_relpath)
            try_makedirs(dirname(in_abspath))
            open(in_abspath, 'w', 'utf-8').write('salut')
            try:
                tasks.transcode(json.dumps(in_relpath))
            except IOError as e:
                if not 'detect resolution' in unicode(e):
                    raise
            ok_(exists(join(LOCAL_DIRECTORY, '1/1/failed/test.txt')))
            ok_(self.is_empty(join(LOCAL_DIRECTORY, '1/1/completed')))
            ok_(self.is_empty(join(LOCAL_DIRECTORY, '1/1/uploaded')))
            ok_(self.is_empty(join(REMOTE_DIRECTORY, '1/1')))

    def test_transcode_mp4(self):
        with mock.patch('encodebox.celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
            from encodebox import tasks
            in_relpath = '1/2/uploaded/test.mp4'
            in_abspath = join(LOCAL_DIRECTORY, in_relpath)
            unguessable = generate_unguessable_filename(SETTINGS['filenames_seed'], 'test.mp4')
            try_makedirs(dirname(in_abspath))
            download('http://techslides.com/demos/sample-videos/small.mp4', in_abspath)
            tasks.transcode(json.dumps(in_relpath))
            ok_(exists(join(LOCAL_DIRECTORY, '1/2/completed/test.mp4')))
            ok_(self.is_empty(join(LOCAL_DIRECTORY, '1/2/failed')))
            ok_(self.is_empty(join(LOCAL_DIRECTORY, '1/2/uploaded')))
            ok_(exists(join(REMOTE_DIRECTORY, '1/2', unguessable + '.smil')))

    def test_transcode_the_media_assets(self):
        with mock.patch('encodebox.celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
            from encodebox import tasks
            media_filenames = sorted(f for f in os.listdir(MEDIA_INPUTS_DIRECTORY) if not f.startswith('.git'))
            for index, filename in enumerate(media_filenames, 1):
                index, name = unicode(index), basename(filename)
                in_relpath = join('2', index, 'uploaded', name)
                in_abspath = join(LOCAL_DIRECTORY, in_relpath)
                unguessable = generate_unguessable_filename(SETTINGS['filenames_seed'], name)
                try_makedirs(dirname(in_abspath))
                shutil.copy(join(MEDIA_INPUTS_DIRECTORY, filename), in_abspath)
                tasks.transcode(json.dumps(in_relpath))
                ok_(exists(join(LOCAL_DIRECTORY, '2', index, 'completed', name)))
                ok_(self.is_empty(join(LOCAL_DIRECTORY, '2', index, 'failed')))
                ok_(self.is_empty(join(LOCAL_DIRECTORY, '2', index, 'uploaded')))
                ok_(exists(join(REMOTE_DIRECTORY, '2', index, unguessable + '.smil')))
                rsync(source=join(REMOTE_DIRECTORY, '2', index), destination=join(MEDIA_REMOTE_DIRECTORY, filename),
                      destination_is_dir=True, archive=True, delete=True, makedest=True, recursive=True)
