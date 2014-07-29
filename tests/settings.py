#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Settings for the unit-tests of EncodeBox.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 CloudNcode Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, yaml
from os.path import abspath, dirname, join, normpath
from encodebox.lib import save_settings

TEST_DIRECTORY = abspath(dirname(__file__))
CONFIG_DIRECTORY = normpath(join(TEST_DIRECTORY, u'..', u'etc'))
LOCAL_DIRECTORY = join(TEST_DIRECTORY, u'local')
MEDIA_DIRECTORY = normpath(join(TEST_DIRECTORY, u'..', u'media'))
MEDIA_INPUTS_DIRECTORY = join(MEDIA_DIRECTORY, u'inputs')
MEDIA_REMOTE_DIRECTORY = join(MEDIA_DIRECTORY, u'remote')
REMOTE_DIRECTORY = join(TEST_DIRECTORY, u'remote')
DIRECTORIES = (u'a/b/c', u'd/e/f/g', u'h')

COMPLETED_FILES = [join(LOCAL_DIRECTORY, d, u'completed', u'file.txt') for d in DIRECTORIES]
OTHER_FILES = [join(LOCAL_DIRECTORY, d, u'other', u'file.txt') for d in DIRECTORIES]

SETTINGS_FILENAME = join(TEST_DIRECTORY, u'settings.yaml')
SETTINGS = yaml.load(open(join(CONFIG_DIRECTORY, 'config.yaml')).read())
SETTINGS.update({
    u'api_servers': None,
    u'email_recipients': None,
    u'completed_cleanup_delay': 1,
    u'local_directory': LOCAL_DIRECTORY,
    u'remote_directory': REMOTE_DIRECTORY,
    u'hd_smil_template': join(CONFIG_DIRECTORY, u'hd.smil'),
    u'sd_smil_template': join(CONFIG_DIRECTORY, u'sd.smil'),
    u'rabbit_password': u'password'
})


def set_test_settings():
    os.environ[u'ENCODEBOX_SETTINGS_FILENAME'] = SETTINGS_FILENAME
    save_settings(SETTINGS_FILENAME, SETTINGS)
