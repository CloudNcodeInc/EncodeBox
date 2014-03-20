#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Settings for the unit-tests of EncodeBox.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
from os.path import abspath, dirname, join
from encodebox.lib import save_settings

TEST_DIRECTORY = abspath(dirname(__file__))
LOCAL_DIRECTORY = join(TEST_DIRECTORY, u'local')
DIRECTORIES = (u'a/b/c', u'd/e/f/g', u'h')

COMPLETED_FILES = [join(LOCAL_DIRECTORY, d, u'completed', u'file.txt') for d in DIRECTORIES]
OTHER_FILES = [join(LOCAL_DIRECTORY, d, u'other', u'file.txt') for d in DIRECTORIES]

SETTINGS_FILENAME = join(TEST_DIRECTORY, u'settings.yaml')
SETTINGS = {
    u'local_directory': LOCAL_DIRECTORY,
    u'completed_cleanup_delay': 1,
    u'rabbit_password': u'password'
}


def set_test_settings():
    os.environ[u'ENCODEBOX_SETTINGS_FILENAME'] = SETTINGS_FILENAME
    save_settings(SETTINGS_FILENAME, SETTINGS)
