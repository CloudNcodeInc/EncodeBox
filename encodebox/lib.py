# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Common utility methods and constants.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, random, re, shlex, shutil, string, sys, yaml
from codecs import open
from os.path import abspath, dirname, exists, expanduser
from pytoolbox.encoding import string_types, to_bytes
from pytoolbox.filesystem import try_makedirs
from subprocess import check_output

HD_HEIGHT = 720
LIB_DIRECTORY = u'/var/encodebox'
SETTINGS_FILENAME = u'/etc/encodebox.yaml'
USERNAME = u'www-data'  # os.getlogin()


def generate_password(chars=None, size=16):
    chars = chars or string.ascii_letters + string.digits
    return u''.join(random.choice(chars) for i in xrange(size))


def load_settings(filename=None, create_directories=False):
    default = os.environ.get(u'ENCODEBOX_SETTINGS_FILENAME', SETTINGS_FILENAME)
    filename = filename or default
    if not exists(filename):
        raise IOError(to_bytes(u'Unable to find settings file "{0}".'.format(filename)))
    with open(filename, u'r', u'utf-8') as f:
        settings = yaml.load(f)
    for key, value in settings.iteritems():
        if u'directory' in key and not u'remote' in key:
            settings[key] = abspath(expanduser(value))
            if create_directories:
                try_makedirs(settings[key])
    return settings


def save_settings(filename, settings):
    with open(filename, u'w', u'utf-8') as f:
        f.write(yaml.safe_dump(settings, default_flow_style=False))


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


def rabbit_users():
    stdout = check_output([u'rabbitmqctl', u'list_users'])
    return re.findall(u'^([a-z]+)\s+.*$', unicode(stdout), re.MULTILINE)


def rabbit_vhosts():
    stdout = check_output([u'rabbitmqctl', u'list_vhosts'])
    return re.findall(u'^([a-z]+)$', unicode(stdout), re.MULTILINE)


def stderr_it(msg, end=u'\n', flush=True):
    sys.stdout.write(u'[ERROR] ' + msg + end)
    if flush:
        sys.stdout.flush()


def stdout_it(msg, end=u'\n', flush=True):
    sys.stdout.write(msg + end)
    if flush:
        sys.stdout.flush()
