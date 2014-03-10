#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from https://bitbucket.org/cloudncode/cloudncode.git
u"""
    Daemon of the EncodeBox launching a new transcoding task for every media asset detected in the input directory.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, time
from os.path import expanduser, isfile, join
from sys import stdout
from .tasks import transcode


# FIXME read configuration from a yaml file
settings = {
    u'inputs_directory': expanduser(u'~/EncodeBox/uploads'),
    u'outputs_directory': expanduser(u'~/EncodeBox/outputs'),
    u'completed_directory': expanduser(u'~/EncodeBox/completed'),
    u'failed_directory': expanduser(u'~/EncodeBox/failed'),
    u'temporary_directory': expanduser(u'~/EncodeBox/temporary'),
    u'hd_transcode_passes': (
        {u'encoder_string': u'-f mp4', u'out_template': u'{username}.{name}.copy1.mp4'},
        {u'encoder_string': u'-f mp4', u'out_template': u'{username}.{name}.copy2.mp4'},
        {u'encoder_string': u'-f mp4', u'out_template': u'{username}.{name}.copy3.mp4'},
        {u'encoder_string': u'-f mp4', u'out_template': u'{username}.{name}.copy4.mp4'},
        {u'encoder_string': u'-f mp4', u'out_template': u'{username}.{name}.copy5.mp4'}
    ),
    u'sd_transcode_passes': (
        {u'encoder_string': u'-f mp4', u'out_template': u'{username}.{name}.copy1.mp4'},
        {u'encoder_string': u'-f mp4', u'out_template': u'{username}.{name}.copy2.mp4'},
        {u'encoder_string': u'-f mp4', u'out_template': u'{username}.{name}.copy3.mp4'}
    )
}


def main():
    start_time = time.time()
    while True:
        stdout.write(u'Already running for {0:0.1f} seconds\n'.format(time.time() - start_time))
        # FIXME use pyinotify instead of recursively scanning (?)
        # FIXME verify if a task is already launched for the file in_relpath
        for in_relpath in os.listdir(settings[u'inputs_directory']):
            if isfile(join(settings[u'inputs_directory'], in_relpath)):
                stdout.write(u'Launch a new transcode task for file "{0}"\n'.format(in_relpath))
                transcode.delay(settings, in_relpath)
        stdout.flush()
        time.sleep(60000)

if __name__ == u'__main__':
    main()
