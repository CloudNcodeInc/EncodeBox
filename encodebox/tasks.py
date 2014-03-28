# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Asynchronous tasks started by the Celery worker.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 CloudNcode Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json, paramiko, os, shutil, time
from celery import Celery
from celery.utils.log import get_task_logger
from codecs import open
from os.path import basename, exists, getsize, join, splitext
from pytoolbox import ffmpeg, x264  # For the line with encoder_module to work!
from pytoolbox.datetime import secs_to_time
from pytoolbox.encoding import configure_unicode, to_bytes
from pytoolbox.ffmpeg import get_media_resolution, HEIGHT
from pytoolbox.filesystem import from_template, try_makedirs
from pytoolbox.subprocess import rsync
from subprocess import check_call

from . import celeryconfig, states
from .lib import load_settings, move, passes_from_template, HD_HEIGHT
from .tasks_lib import TranscodeProgressReport

configure_unicode()

app = Celery(u'tasks')
app.config_from_object(celeryconfig)


@app.task(name=u'encodebox.tasks.transcode')
def transcode(in_relpath_json):
    u"""Convert an input media file to 3 (SD) or 5 (HD) output files."""

    logger = get_task_logger(u'encodebox.tasks.transcode')
    report = None
    in_abspath = None
    failed_abspath = None
    temporary_directory = None
    outputs_directory = None
    final_state = states.FAILURE
    final_url = None
    try:
        settings = load_settings()
        in_relpath = json.loads(in_relpath_json)
        in_abspath = join(settings[u'local_directory'], in_relpath)
        try:
            in_directories = in_relpath.split(os.sep)
            assert(len(in_directories) == 4)
            publisher_id = in_directories[0]
            product_id = in_directories[1]
            assert(in_directories[2] == u'uploaded')
            filename = in_directories[3]
            name, extension = splitext(filename)
        except:
            raise ValueError(to_bytes(u'Input file path does not respect template publisher_id/product_id/filename'))

        completed_abspath = join(settings[u'local_directory'], publisher_id, product_id, u'completed', filename)
        failed_abspath = join(settings[u'local_directory'], publisher_id, product_id, u'failed', filename)
        temporary_directory = join(settings[u'local_directory'], publisher_id, product_id, u'temporary', filename)
        outputs_directory = join(settings[u'local_directory'], publisher_id, product_id, u'outputs', filename)
        remote_directory = join(settings[u'remote_directory'], publisher_id, product_id)
        remote_url = settings[u'remote_url'].format(publisher_id=publisher_id, product_id=product_id, name=name)

        report = TranscodeProgressReport(settings[u'api_url'], settings[u'api_auth'], publisher_id, product_id,
                                         filename, getsize(in_abspath), logger)
        report.send_report(states.STARTED, counter=0)

        logger.info(u'Create outputs directories')

        for path in (completed_abspath, failed_abspath, temporary_directory, outputs_directory):
            shutil.rmtree(path, ignore_errors=True)
        try_makedirs(temporary_directory)
        try_makedirs(outputs_directory)

        resolution = get_media_resolution(in_abspath)
        if not resolution:
            raise IOError(to_bytes(u'Unable to detect resolution of video "{0}"'.format(in_relpath)))

        quality = u'hd' if resolution[HEIGHT] >= HD_HEIGHT else u'sd'
        template_transcode_passes = settings[quality + u'_transcode_passes']
        template_smil_filename = settings[quality + u'_smil_template']

        logger.info(u'Media {0} {1}p {2}'.format(quality.upper(), resolution[HEIGHT], in_relpath))

        logger.info(u'Generate SMIL file from template SMIL file')
        from_template(template_smil_filename, join(outputs_directory, name + u'.smil'), {u'name': name})

        logger.info(u'Generate transcoding passes from templated transcoding passes')
        transcode_passes = passes_from_template(template_transcode_passes, input=in_abspath, name=name,
                                                out=outputs_directory, tmp=temporary_directory)
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
                try:
                    check_call(transcode_pass)
                except OSError:
                    raise OSError(to_bytes(u'Missing encoder ' + transcode_pass[0]))

        logger.info(u'Move the input file to the completed directory and send outputs to the remote host')
        move(in_abspath, completed_abspath)
        try:
            report.send_report(states.TRANSFERRING)
            username_host, directory = remote_directory.split(u':')
            username, host = username_host.split(u'@')
            ssh_client = paramiko.SSHClient()
            ssh_client.load_system_host_keys()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # FIXME man-in-the-middle attack
            ssh_client.connect(host, username=username)
            ssh_client.exec_command(u'mkdir -p "{0}"'.format(directory))
            rsync(source=outputs_directory, destination=remote_directory, source_is_dir=True, destination_is_dir=True,
                  archive=True, delete=True, progress=True, recursive=True, extra=u'ssh')
            final_state, final_url = states.SUCCESS, remote_url
        except Exception as e:
            logger.exception(u'Transfer of outputs to remote host failed')
            final_state = states.TRANSFER_ERROR
            with open(join(outputs_directory, u'transfer-error.log'), u'w', u'utf-8') as log:
                log.write(repr(e))
    except:
        logger.exception(u'Transcoding task failed')
        logger.info(u'Move the input file to the failed directory and remove the outputs')
        if in_abspath and failed_abspath:
            move(in_abspath, failed_abspath)
        if outputs_directory and exists(outputs_directory):
            shutil.rmtree(outputs_directory)
        raise
    finally:
        if report:
            report.send_report(final_state, url=final_url)
        logger.info(u'Remove the temporary files')
        if temporary_directory and exists(temporary_directory):
            shutil.rmtree(temporary_directory)


@app.task(name=u'encodebox.tasks.cleanup')
def cleanup():

    logger = get_task_logger(u'encodebox.tasks.cleanup')
    try:
        settings = load_settings()
        delay = settings[u'completed_cleanup_delay']
        max_mtime = time.time() - delay
        removed = set()
        for root, dirnames, filenames in os.walk(settings[u'local_directory']):
            if basename(root) == u'completed':
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
