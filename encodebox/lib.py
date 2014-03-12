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

import shlex, shutil, sys, yaml
from codecs import open
from os.path import abspath, dirname, expanduser
from pytoolbox.encoding import string_types, to_bytes
from pytoolbox.filesystem import first_that_exist, try_makedirs

HD_HEIGHT = 720
LIB_DIRECTORY = u'/var/encodebox'
SETTINGS_FILENAMES = (u'/etc/encodebox.yaml', u'etc/encodebox.yaml')


def load_settings(create_directories=False):
    filename = first_that_exist(*SETTINGS_FILENAMES)
    if not filename:
        raise IOError(to_bytes(u'Unable to find any settings file.'))
    with open(filename, u'r', u'utf-8') as f:
        settings = yaml.load(f)
    for key, value in settings.iteritems():
        if u'directory' in key and not u'remote' in key:
            settings[key] = abspath(expanduser(value))
            if create_directories:
                try_makedirs(settings[key])
    return settings, filename


def move(source, destination):
    u"""
    Create the destination directory if missing and recursively move a file/directory from source to destination.

    **Example usage**

    >>> import os
    >>> open(u'/tmp/move_test_file', u'w', u'utf-8').close()
    >>> move(u'/tmp/move_test_file', u'/tmp/move_demo/another/file')
    >>> os.remove(u'/tmp/move_demo/another/file')
    >>> shutil.rmtree(u'/tmp/move_demo')
    """
    try_makedirs(dirname(destination))
    shutil.move(source, destination)


def passes_from_template(template_passes, **kwargs):
    u"""
    Return a list of (transcoding) passes with {variables} replaced by the values in kwargs.

    **Example usage**

    >>> import os
    >>> templated_passes = [
    ...     [u'ffmpeg', [u'{video}', u'{audio}'], u'{tmp}/a.wav', u'-analyzeduration 2147480000 -ar 48000 -ac 2'],
    ...     u'neroAacEnc -cbr 128000 -lc -if "{tmp}/été.wav" -of "{tmp}/été.mp4"',
    ...     [u'x264', u'{tmp}/vidéo.y4m', None, u'--pass 1 --fps 25 --bitrate 2000 --no-scenecut']
    ... ]
    >>> passes = passes_from_template(templated_passes, video=u'tabby.h264', audio=u'miaow.aac', tmp=u'/tmp')
    >>> for p in passes:
    ...     print(p)
    [u'ffmpeg', [u'tabby.h264', u'miaow.aac'], u'/tmp/a.wav', u'-analyzeduration 2147480000 -ar 48000 -ac 2']
    [u'neroAacEnc', u'-cbr', u'128000', u'-lc', u'-if', u'/tmp/\\xe9t\\xe9.wav', u'-of', u'/tmp/\\xe9t\\xe9.mp4']
    [u'x264', u'/tmp/vid\\xe9o.y4m', None, u'--pass 1 --fps 25 --bitrate 2000 --no-scenecut']

    Verify that Unicode filenames are handled correctly:

    >>> open(u'/tmp/vidéo.y4m', u'a').close()
    >>> os.remove(passes[2][1])
    """
    passes = []
    for template_pass in template_passes:
        if isinstance(template_pass, string_types):
            values = shlex.split(to_bytes(template_pass.format(**kwargs)))
            passes.append([unicode(v, u'utf-8') for v in values])
        else:
            the_pass = []
            for value in template_pass:
                if value is None:
                    the_pass.append(value)
                elif isinstance(value, string_types):
                    the_pass.append(value.format(**kwargs))
                else:
                    the_pass.append([x.format(**kwargs) for x in value])
            passes.append(the_pass)
    return passes


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
