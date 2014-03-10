#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# This file is part of EncodeBox Project, retrieved from <TODO address of the repository>
u"""
    Common utility methods and constants.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import shutil
from os.path import basename, dirname, splitext
from pytoolbox.filesystem import try_makedirs

WIDTH, HEIGHT = range(2)
HD_HEIGHT = 720


# def create_directories(settings):
#     u"""Create the directories retrieved from settings."""
#     for name, value in settings.iteritems():
#         if u'directory' in name:
#             try_makedirs(value)


def get_media_size(tracks):
    u"""Return [width, height] of the first video track in ``tracks`` or None."""
    try:
        first_video_track = next(tracks[u'video'].itervalues())
        size = [int(n) for n in first_video_track[u'size'].split(u'x')]
        assert(len(size) == 2)
        return size
    except (AssertionError, KeyError, ValueError):
        return None


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
