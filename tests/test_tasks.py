# -*- coding: utf-8 -*-

# Base Application of the CloudNcode SaaS Transcoding Platform
# Retrieved from https://bitbucket.org/cloudncode/cloudncode.git
u"""
    Test the tasks of the CloudNcode base application.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 CloudNcode Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import mock, shutil, time
from codecs import open
from nose.tools import eq_, ok_
from os.path import exists
from pytoolbox.filesystem import try_makedirs, try_remove
from .settings import set_test_settings, COMPLETED_DIRECTORY, SETTINGS_FILENAME, TEST_FILES


class TestTasks(object):

    def setUp(self):
        set_test_settings()
        try_makedirs(COMPLETED_DIRECTORY)

    def tearDown(self):
        try_remove(SETTINGS_FILENAME)
        shutil.rmtree(COMPLETED_DIRECTORY)

    def create_files(self):
        for test_file in TEST_FILES:
                    with open(test_file, u'w', u'utf-8') as f:
                        f.write(u'some content for the test')

    def create_or_update_file(self, index):
        with open(TEST_FILES[index], u'a', u'utf-8') as f:
            f.write(u'an update')

    def test_mock_settings_works(self):
        with mock.patch(u'encodebox.celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
            from encodebox import tasks
            result = tasks.cleanup.apply()
            ok_(result.failed())
            eq_(type(result.result), IOError)

    def test_cleanup_empty_directories(self):
        with mock.patch(u'encodebox.celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
            from encodebox import tasks
            result = tasks.cleanup.apply()
            ok_(result.successful())
            eq_(result.result, set())

    def test_cleanup_0_files(self):
        with mock.patch(u'encodebox.celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
            from encodebox import tasks
            self.create_files()
            result = tasks.cleanup.apply()
            ok_(result.successful())
            eq_(result.result, set())

    def test_cleanup_all_files(self):
        with mock.patch(u'encodebox.celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
            from encodebox import tasks
            self.create_files()
            time.sleep(2)
            result = tasks.cleanup.apply()
            ok_(result.successful())
            eq_(len(result.result), len(TEST_FILES))
            for test_file in TEST_FILES:
                ok_(not exists(test_file))

    def test_cleanup_complex_scenario(self):
        with mock.patch(u'encodebox.celeryconfig.CELERY_ALWAYS_EAGER', True, create=True):
            from encodebox import tasks

            self.create_files()
            time.sleep(1.1)
            self.create_or_update_file(0)
            result = tasks.cleanup.apply()
            ok_(result.successful())
            eq_(result.result, set(TEST_FILES[1:]))
            for index, test_file in enumerate(TEST_FILES):
                ok_(exists(test_file) == (index == 0))

            time.sleep(0.7)
            self.create_or_update_file(1)
            time.sleep(0.3)
            self.create_or_update_file(2)
            time.sleep(0.3)
            result = tasks.cleanup.apply()
            ok_(result.successful())
            eq_(result.result, set([TEST_FILES[0]]))

            time.sleep(0.5)
            result = tasks.cleanup.apply()
            ok_(result.successful())
            eq_(result.result, set([TEST_FILES[1]]))

            time.sleep(0.5)
            result = tasks.cleanup.apply()
            ok_(result.successful())
            eq_(result.result, set([TEST_FILES[2]]))
            for index, test_file in enumerate(TEST_FILES):
                ok_(not exists(test_file))
