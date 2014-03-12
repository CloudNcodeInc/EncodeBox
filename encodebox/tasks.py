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

import json, os, shutil, sys, time
from celery import Celery
from os.path import basename, exists, join, splitext
from pytoolbox import ffmpeg, x264  # For the line with encoder_module to work!
from pytoolbox.datetime import secs_to_time
from pytoolbox.encoding import configure_unicode, to_bytes
from pytoolbox.ffmpeg import get_media_resolution, HEIGHT
from pytoolbox.filesystem import try_makedirs
from subprocess import check_call

from . import celeryconfig
from .lib import load_settings, move, passes_from_template, sanitize_filename, HD_HEIGHT

configure_unicode()

app = Celery(u'tasks')
app.config_from_object(celeryconfig)


@app.task(name=u'encodebox.tasks.transcode')
def transcode(in_relpath_json):
    u"""Convert an input media file to 3 (SD) or 5 (HD) output files."""

    def print_it(message, **kwargs):
        print(u'{0} {1}'.format(transcode.request.id, message), **kwargs)

    in_abspath = None
    in_relpath = None
    task_temporary_directory = None
    task_outputs_directory = None
    try:
        settings, _ = load_settings()
        in_relpath = json.loads(in_relpath_json)
        in_abspath = join(settings[u'inputs_directory'], in_relpath)

        print_it(u'Create outputs directories')
        task_temporary_directory = join(settings[u'temporary_directory'], transcode.request.id)
        task_outputs_directory = join(settings[u'outputs_directory'], transcode.request.id)
        try_makedirs(task_temporary_directory)
        try_makedirs(task_outputs_directory)

        resolution = get_media_resolution(in_abspath)
        if not resolution:
            raise IOError(to_bytes(u'Unable to detect resolution of video "{0}"'.format(in_relpath)))

        quality = u'hd' if resolution[HEIGHT] >= HD_HEIGHT else u'sd'
        template_transcode_passes = settings[quality + u'_transcode_passes']
        total = len(template_transcode_passes)

        print_it(u'Media {0} {1}p {2}'.format(quality.upper(), resolution[HEIGHT], in_relpath))

        print_it(u'Generate transcoding passes from templated transcoding passes')
        transcode_passes = passes_from_template(template_transcode_passes, input=in_abspath,
                                                name=sanitize_filename(splitext(basename(in_relpath))[0]),
                                                out=task_outputs_directory, tmp=task_temporary_directory)
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
        if in_abspath and in_relpath:
            move(in_abspath, join(settings[u'failed_directory'], in_relpath))
        # Cleanup all outputs and re-raise the exception
        print_it(u'Remove the output files')
        if task_outputs_directory and exists(task_outputs_directory):
            shutil.rmtree(task_outputs_directory)
        raise
    finally:
        print_it(u'Remove the temporary files')
        if task_temporary_directory and exists(task_temporary_directory):
            shutil.rmtree(task_temporary_directory)

# [1]: See TODO list for a potentially better way to send the reports


@app.task(name=u'encodebox.tasks.cleanup')
def cleanup():

    def print_it(message, **kwargs):
        print(u'{0} {1}'.format(cleanup.request.id, message), **kwargs)

    try:
        settings, _ = load_settings()
        delay = settings[u'completed_cleanup_delay']
        max_mtime = time.time() - delay
        removed = set()
        for root, dirnames, filenames in os.walk(settings[u'completed_directory']):
            for filename in filenames:
                filename = join(root, filename)
                if os.stat(filename).st_mtime < max_mtime:
                    print_it(u'Remove file older than {0} {1}'.format(secs_to_time(delay), filename))
                    os.remove(filename)
                    removed.add(filename)
        return removed
    except Exception as e:
        print_it(u'[ERROR] Something went wrong, reason: {0}'.format(repr(e)), file=sys.stderr)
        raise
