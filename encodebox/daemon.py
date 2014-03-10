#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Daemon of the EncodeBox launching a new transcoding task for every media asset detected in the input directory.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, time, yaml
from codecs import open
from os.path import abspath, expanduser, isfile, join
from pytoolbox.filesystem import first_that_exist, try_makedirs
from sys import exit, stderr, stdout
from .tasks import transcode


def main():
    try:
        start_time = time.time()
        settings_filename = first_that_exist(u'/etc/encodebox.yaml', u'etc/encodebox.yaml')
        stdout.write(u'Read settings from {0}\n'.format(settings_filename))
        stdout.flush()
        with open(settings_filename, u'r', u'utf-8') as f:
            settings = yaml.load(f)
        stdout.write(u'Create the watch-folder directories\n')
        stdout.flush()
        for key, value in settings.iteritems():
            if u'directory' in key:
                settings[key] = directory = abspath(expanduser(value))
                try_makedirs(directory)
        while True:
            stdout.write(u'Already running for {0:0.1f} seconds\n'.format(time.time() - start_time))
            # FIXME use pyinotify instead of recursively scanning (?)
            # FIXME verify if a task is already launched for the file in_relpath
            for in_relpath in os.listdir(settings[u'inputs_directory']):
                if isfile(join(settings[u'inputs_directory'], in_relpath)):
                    stdout.write(u'Launch a new transcode task for file "{0}"\n'.format(in_relpath))
                    transcode.delay(settings, in_relpath)
            stdout.flush()
            #time.sleep(60000)
            exit(0)
    except Exception as e:
        stderr.write(u'[ERROR] {0}\n'.format(e))
        stderr.flush()
        exit(1)

if __name__ == u'__main__':
    main()
