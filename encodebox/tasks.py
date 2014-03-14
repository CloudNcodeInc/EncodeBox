# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Asynchronous tasks started by the Celery worker.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json, os, shutil, time
from celery import Celery
from celery.utils.log import get_task_logger
from os.path import basename, exists, join, splitext
from pytoolbox import ffmpeg, x264  # For the line with encoder_module to work!
from pytoolbox.datetime import secs_to_time
from pytoolbox.encoding import configure_unicode, to_bytes
from pytoolbox.ffmpeg import get_media_resolution, HEIGHT
from pytoolbox.filesystem import try_makedirs
from subprocess import check_call

from . import celeryconfig, states
from .lib import load_settings, move, passes_from_template, sanitize_filename, HD_HEIGHT
from .tasks_lib import TranscodeProgressReport

configure_unicode()

app = Celery(u'tasks')
app.config_from_object(celeryconfig)
logger = get_task_logger(__name__)


@app.task(name=u'encodebox.tasks.transcode')
def transcode(in_relpath_json):
    u"""Convert an input media file to 3 (SD) or 5 (HD) output files."""

    report = None
    successful = False
    in_abspath = None
    in_relpath = None
    task_temporary_directory = None
    task_outputs_directory = None
    try:
        settings, _ = load_settings()
        in_relpath = json.loads(in_relpath_json)
        in_abspath = join(settings[u'inputs_directory'], in_relpath)
        try:
            in_directories = in_relpath.split(os.sep)
            assert(len(in_directories) == 3)
            user_id = in_directories[0]
            content_id = in_directories[1]
            name = in_directories[2]
        except:
            raise ValueError(to_bytes(u'Input file path does not respect template user_id/content_id/name'))

        report = TranscodeProgressReport(settings[u'api_url'], settings[u'api_auth'], user_id, content_id, name, logger)

        logger.info(u'Create outputs directories')
        task_temporary_directory = join(settings[u'temporary_directory'], user_id, content_id)
        task_outputs_directory = join(settings[u'outputs_directory'], user_id, content_id)
        try_makedirs(task_temporary_directory)
        try_makedirs(task_outputs_directory)

        resolution = get_media_resolution(in_abspath)
        if not resolution:
            raise IOError(to_bytes(u'Unable to detect resolution of video "{0}"'.format(in_relpath)))

        quality = u'hd' if resolution[HEIGHT] >= HD_HEIGHT else u'sd'
        template_transcode_passes = settings[quality + u'_transcode_passes']

        logger.info(u'Media {0} {1}p {2}'.format(quality.upper(), resolution[HEIGHT], in_relpath))

        logger.info(u'Generate transcoding passes from templated transcoding passes')
        transcode_passes = passes_from_template(template_transcode_passes, input=in_abspath,
                                                name=sanitize_filename(splitext(basename(in_relpath))[0]),
                                                out=task_outputs_directory, tmp=task_temporary_directory)
        report.transcode_passes = transcode_passes

        logger.info(u'Execute transcoding passes')
        for counter, transcode_pass in enumerate(transcode_passes, 1):
            if transcode_pass[0] in (u'ffmpeg', u'x264'):
                encoder_module = globals()[transcode_pass[0]]
                for statistics in encoder_module.encode(transcode_pass[1], transcode_pass[2], transcode_pass[3]):
                    status = statistics.pop(u'status').upper()
                    if status == u'PROGRESS':
                        for info in (u'output', u'returncode', u'sanity'):
                            statistics.pop(info, None)
                        report.send_report(states.ENCODING, counter=counter, statistics=statistics)
                    elif status == u'ERROR':
                        raise RuntimeError(statistics)
            else:
                check_call(transcode_pass)

        logger.info(u'Move the input file to the completed directory and send outputs to the remote host')
        move(in_abspath, join(settings[u'completed_directory'], in_relpath))
        #rsync(source=task_outputs_directory, desination=join(settings[u'completed_remote_directory'], task_id),
        #      source_is_dir=True, destination_is_dir=True, archive=True, progress=True, recursive=True, extra=u'e ssh')
        successful = True
    except:
        logger.exception(u'Transcoding task failed')
        logger.info(u'Move the input file to the failed directory and remove the outputs')
        if in_abspath and in_relpath:
            move(in_abspath, join(settings[u'failed_directory'], in_relpath))
        if task_outputs_directory and exists(task_outputs_directory):
            shutil.rmtree(task_outputs_directory)
        raise
    finally:
        if report:
            report.send_report(states.SUCCESS if successful else states.FAILURE)
        logger.info(u'Remove the temporary files')
        if task_temporary_directory and exists(task_temporary_directory):
            shutil.rmtree(task_temporary_directory)


@app.task(name=u'encodebox.tasks.cleanup')
def cleanup():

    try:
        settings, _ = load_settings()
        delay = settings[u'completed_cleanup_delay']
        max_mtime = time.time() - delay
        removed = set()
        for root, dirnames, filenames in os.walk(settings[u'completed_directory']):
            for filename in filenames:
                filename = join(root, filename)
                if os.stat(filename).st_mtime < max_mtime:
                    logger.info(u'Remove file older than {0} {1}'.format(secs_to_time(delay), filename))
                    os.remove(filename)
                    removed.add(filename)
        return removed
    except:
        logger.exception(u'Cleanup task failed')
        raise
