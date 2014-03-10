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

import json, sys
from celery import Celery
from os.path import dirname, join
from pytoolbox.datetime import secs_to_time
from pytoolbox.encoding import configure_unicode, to_bytes
from pytoolbox.ffmpeg import encode, get_media_resolution, HEIGHT
from pytoolbox.filesystem import try_makedirs, try_remove
from pytoolbox.subprocess import rsync
from .lib import get_out_relpath, move, HD_HEIGHT

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
        transcode_passes = settings[quality + u'_transcode_passes']
        total = len(transcode_passes)

        print_it(u'Media {0} {1}p {2}'.format(quality.upper(), resolution[HEIGHT], in_relpath))

        for counter, transcode_pass in enumerate(transcode_passes, 1):
            username = u'toto'  # FIXME detect username based on input directory name (?)
            out_relpath = get_out_relpath(transcode_pass[u'out_template'], username, in_relpath)
            tmp_abspath = join(task_temporary_directory, out_relpath)
            out_abspath = join(task_outputs_directory,   out_relpath)
            encoder_string = transcode_pass[u'encoder_string']

            print_it(u'Pass {0} of {1} : Convert to {2}'.format(counter, total, out_relpath))

            # Transcode the input media file into the temporary directory
            try_makedirs(dirname(tmp_abspath))
            for statistics in encode(in_abspath, tmp_abspath, encoder_string):
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
                # {u'quality': '29.0', u'out_duration': '00:02:47.93', u'percent': 79, u'frame': '5096',
                # u'eta_time': 18, u'elapsed_time': 72.38623189926147, u'bitrate': '1788.4kbits/s', u'fps': '70',
                # u'out_size': 37542493, u'in_duration': u'00:03:31.25', u'in_size': 52899452,
                # u'start_date': u'2014-03-07 16:03:52'}
                # FIXME #4 POST current pass progress report to remote API [1]

            # Move the temporary file to the outputs directory and POST the success report to remote API
            move(tmp_abspath, out_abspath)
            # FIXME #4 POST current pass success report to remote API [1]

        print_it(u'Move the input file to the completed directory and send outputs to the remote host')
        move(in_abspath, join(settings[u'completed_directory'], in_relpath))
        rsync(source=task_outputs_directory, desination=join(settings[u'completed_remote_directory'], task_id),
              source_is_dir=True, destination_is_dir=True, archive=True, progress=True, recursive=True, extra=u'e ssh')
        # FIXME #4 POST success report to remote API [1]
    except Exception as e:
        print_it(u'[ERROR] Something went wrong, reason: {0}'.format(repr(e)), file=sys.stderr)
        # Move the input file to the failed directory and POST the error report to remote API
        # FIXME #4 POST error report to remote API [1]
        move(in_abspath, join(settings[u'failed_directory'], in_relpath))
        # Cleanup all outputs and re-raise the exception
        try_remove(task_temporary_directory)
        try_remove(task_outputs_directory)
        raise

# [1]: See TODO list for a potentially better way to send the reports
