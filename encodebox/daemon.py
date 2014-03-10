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

import json, os, pyinotify, sys, yaml
from codecs import open
from os.path import abspath, expanduser
from pytoolbox.filesystem import first_that_exist, try_makedirs
from .lib import stdout_it, stderr_it
from .tasks import transcode


def main():
    global settings
    try:
        settings_filename = first_that_exist(u'/etc/encodebox.yaml', u'etc/encodebox.yaml')
        stdout_it(u'Read settings from ' + settings_filename)
        with open(settings_filename, u'r', u'utf-8') as f:
            settings = yaml.load(f)
        stdout_it(u'Create the watch-folder directories')
        for key, value in settings.iteritems():
            if u'directory' in key:
                settings[key] = directory = abspath(expanduser(value))
                try_makedirs(directory)
        manager = pyinotify.WatchManager()
        manager.add_watch(settings[u'inputs_directory'], pyinotify.IN_CLOSE_WRITE, rec=True)
        handler = InputsHandler()
        handler.settings = settings
        notifier = pyinotify.Notifier(manager, handler)
        notifier.loop()
        sys.exit(0)
    except Exception as e:
        stderr_it(unicode(e))
        sys.exit(1)


class InputsHandler(pyinotify.ProcessEvent):

    def process_IN_CLOSE_WRITE(self, event):
        u"""Launch a new transcoding task for the updated input media file."""
        in_relpath = event.pathname.replace(self.settings[u'inputs_directory'] + os.sep, u'')
        stdout_it(u'Launch a new transcode task for file "{0}"\n'.format(in_relpath))
        transcode.delay(json.dumps(self.settings), json.dumps(in_relpath))

    # def garbage():
    #     from os.path import abspath, expanduser, isfile, join
    #     stdout.write(u'Already running for {0:0.1f} seconds\n'.format(time.time() - start_time))
    #     # FIXME use pyinotify instead of recursively scanning (?)
    #     # FIXME verify if a task is already launched for the file in_relpath
    #     for in_relpath in os.listdir(settings[u'inputs_directory']):
    #         if isfile(join(settings[u'inputs_directory'], in_relpath)):
    #             stdout.write(u'Launch a new transcode task for file "{0}"\n'.format(in_relpath))
    #             transcode.delay(settings, in_relpath)
    #     stdout.flush()
    #     #time.sleep(60000)
    #     exit(0)


if __name__ == u'__main__':
    main()
