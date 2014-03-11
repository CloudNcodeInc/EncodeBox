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

import shlex, shutil, sys
from os.path import dirname
from pytoolbox.encoding import string_types
from pytoolbox.filesystem import try_makedirs

HD_HEIGHT = 720


def move(source, destination):
    try_makedirs(dirname(destination))
    shutil.move(source, destination)


def passes_from_template(template_passes, **kwargs):
    passes = []
    for template_pass in template_passes:
        if isinstance(template_pass, string_types):
            passes.append(shlex.split(template_pass.format(**kwargs)))
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
