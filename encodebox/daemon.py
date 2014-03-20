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

import json, os, pyinotify, sys
#from celery import current_app as celery
from os.path import basename, dirname
from .lib import load_settings, stdout_it, stderr_it
from .tasks import transcode


def main():
    try:
        stdout_it(u'Read settings and create watch-folder directories')
        settings = load_settings(create_directories=True)
        manager = pyinotify.WatchManager()
        manager.add_watch(settings[u'local_directory'], pyinotify.ALL_EVENTS, rec=True, auto_add=True)
        handler = InputsHandler()
        handler.settings = settings
        notifier = pyinotify.Notifier(manager, handler)
        notifier.loop()
        sys.exit(0)
    except Exception as e:
        stderr_it(unicode(e))
        sys.exit(1)


class InputsHandler(pyinotify.ProcessEvent):

    #def __init__(self, *args, **kwargs):
    #    super(InputsHandler, self).__init__(*args, **kwargs)
    #    self.tasks = {}

    def process_IN_CLOSE_WRITE(self, event):
        try:
            u"""Launch a new transcoding task for the updated input media file."""
            in_relpath = event.pathname.replace(self.settings[u'local_directory'] + os.sep, u'')
            if basename(dirname(in_relpath)) == u'uploaded':
                stdout_it(u'Launch a new transcode task for file "{0}"\n'.format(in_relpath))
                #task_id = self.tasks.pop(in_relpath, None)
                #if task_id:
                #    stdout_it(u'Revoke previous task with id "{0}"'.format(task_id))
                #    celery.control.revoke(task_id, terminate=True)
                #self.tasks[in_relpath] = transcode.delay(json.dumps(in_relpath)).id
                transcode.delay(json.dumps(in_relpath))
        except Exception as e:
            stderr_it(unicode(e))
            raise

if __name__ == u'__main__':
    main()
