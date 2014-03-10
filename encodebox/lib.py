#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Common utility methods and constants.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import shutil, sys
from os.path import basename, dirname, splitext
from pytoolbox.filesystem import try_makedirs

HD_HEIGHT = 720


def get_out_relpath(template, username, in_relpath):
    name, extension = splitext(basename(in_relpath))
    name = sanitize_filename(name).lower()
    return template.format(username=username, name=name, extension=extension)


def move(source, destination):
    try_makedirs(dirname(destination))
    shutil.move(source, destination)


def sanitize_filename(filename):
    # FIXME implement a better filename sanitizer
    return filename.replace(u'&', u'').replace(u'[', u'').replace(u']', u'').replace(u' ', u'_')


def stderr_it(msg, end=u'\n', flush=True):
    sys.stdout.write(u'[ERROR] ' + msg + end)
    if flush:
        sys.stdout.flush()


def stdout_it(msg, end=u'\n', flush=True):
    sys.stdout.write(msg + end)
    if flush:
        sys.stdout.flush()
