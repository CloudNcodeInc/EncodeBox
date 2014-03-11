#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Asynchronous tasks started by the Celery worker.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json, os, shutil, sys
from celery import Celery
from os.path import basename, join, splitext
from pytoolbox import ffmpeg, x264  # For the line with encoder_module to work!
from pytoolbox.datetime import secs_to_time
from pytoolbox.encoding import configure_unicode, to_bytes
from pytoolbox.ffmpeg import get_media_resolution, HEIGHT
from pytoolbox.filesystem import try_makedirs
from pytoolbox.subprocess import rsync
from subprocess import check_call
from .lib import move, passes_from_template, sanitize_filename, HD_HEIGHT

configure_unicode()

app = Celery(u'tasks', broker=u'amqp://guest@localhost//')
app.conf.CELERY_ACCEPT_CONTENT = [u'json']
app.conf.CELERY_TASK_SERIALIZER = u'json'


@app.task(name=u'encodebox.tasks.transcode')
def transcode(settings_json, in_relpath_json):
    u"""Convert an input media file to 3 (SD) or 5 (HD) output files."""

    def print_it(message, **kwargs):
        print(u'{0} {1}'.format(transcode.request.id, message), **kwargs)

    settings = json.loads(settings_json)
    in_relpath = json.loads(in_relpath_json)
    in_abspath = join(settings[u'inputs_directory'], in_relpath)
    task_id = transcode.request.id
    task_temporary_directory = join(settings[u'temporary_directory'], task_id)
    task_outputs_directory = join(settings[u'outputs_directory'], task_id)
    try:
        resolution = get_media_resolution(in_abspath)
        if not resolution:
            raise IOError(to_bytes(u'Unable to detect resolution of video "{0}"'.format(in_relpath)))

        quality = u'hd' if resolution[HEIGHT] >= HD_HEIGHT else u'sd'
        template_transcode_passes = settings[quality + u'_transcode_passes']
        total = len(template_transcode_passes)

        print_it(u'Media {0} {1}p {2}'.format(quality.upper(), resolution[HEIGHT], in_relpath))

        print_it(u'Create outputs directories')
        try_makedirs(task_temporary_directory)
        try_makedirs(task_outputs_directory)

        print_it(u'Generate transcoding passes from templated transcoding passes')
        transcode_passes = passes_from_template(
            template_transcode_passes, input=in_abspath, name=sanitize_filename(splitext(basename(in_relpath))[0]),
            out=task_outputs_directory + os.sep, tmp=task_temporary_directory + os.sep)
        total = len(template_transcode_passes)

        print_it(u'Execute transcoding passes')
        for counter, transcode_pass in enumerate(transcode_passes, 1):
            print(u'Execute pass {0} of {1} : {2}'.format(counter, total, transcode_pass))
            if transcode_pass[0] in (u'ffmpeg', u'x264'):
                encoder_module = globals()[transcode_pass[0]]
                for statistics in encoder_module.encode(transcode_pass[1], transcode_pass[2], transcode_pass[3]):
                    status = statistics.pop(u'status').upper()
                    if status == u'PROGRESS':
                        for info in (u'output', u'returncode', u'sanity'):
                            statistics.pop(info, None)
                    elif status == u'ERROR':
                        raise RuntimeError(statistics)
                    transcode.update_state(state=status, meta=statistics)
                    print_it(u'Pass {counter} of {total} : Progress {percent}% {elapsed} ETA {eta}'.format(
                             counter=counter, total=total, percent=statistics.get(u'percent', u'unknown'),
                             elapsed=secs_to_time(statistics.get(u'elapsed_time', 0)),
                             eta=secs_to_time(statistics.get(u'eta_time', 0))))
            else:
                check_call(transcode_pass)
            # FIXME #4 POST current pass success report to remote API [1]

        print_it(u'Move the input file to the completed directory and send outputs to the remote host')
        move(in_abspath, join(settings[u'completed_directory'], in_relpath))
        #rsync(source=task_outputs_directory, desination=join(settings[u'completed_remote_directory'], task_id),
        #      source_is_dir=True, destination_is_dir=True, archive=True, progress=True, recursive=True, extra=u'e ssh')
        # FIXME #4 POST success report to remote API [1]
    except Exception as e:
        print_it(u'[ERROR] Something went wrong, reason: {0}'.format(repr(e)), file=sys.stderr)
        # Move the input file to the failed directory and POST the error report to remote API
        # FIXME #4 POST error report to remote API [1]
        move(in_abspath, join(settings[u'failed_directory'], in_relpath))
        # Cleanup all outputs and re-raise the exception
        print_it(u'Remove the output files')
        shutil.rmtree(task_outputs_directory)
        raise
    finally:
        print_it(u'Remove the temporary files')
        shutil.rmtree(task_temporary_directory)

# [1]: See TODO list for a potentially better way to send the reports
