# -*- encoding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Utility library of the asynchronous tasks started by the Celery worker.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 CloudNcode Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json, requests, time
from codecs import open
from jinja2 import Template
from pytoolbox.datetime import secs_to_time

from .lib import send_email


class TranscodeProgressReport(object):

    def __init__(self, api_servers, publisher_id, product_id, filename, original_size, logger):
        self.api_servers = api_servers
        self.publisher_id = publisher_id
        self.product_id = product_id
        self.filename = filename
        self.original_size = original_size
        self.logger = logger
        self.start_time = time.time()
        self.transcode_passes = {}

    @property
    def total(self):
        return len(self.transcode_passes)

    def send_report(self, state, url=None, counter=None, statistics=None):
        if counter is None:
            counter = self.total
        if statistics is None:
            statistics = {}
        task_elapsed = time.time() - self.start_time
        pass_progress = max(0, min(1, float(statistics.get(u'percent', 100)) / 100))
        task_progress = max(0, min(1, (counter - 1 + pass_progress) / self.total)) if self.total > 0 else 1
        task_eta = int(task_elapsed * (1 - task_progress) / task_progress) if task_progress > 0 else 0
        self.logger.info(u'{state} {task_progress:0.0%} {task_elapsed} ETA {task_eta} - Pass {counter} of {total} : '
                         u'{pass_progress:0.0%} {pass_elapsed} ETA {pass_eta} {pass_fps} fps'.format(
                         state=state, task_progress=task_progress, task_elapsed=secs_to_time(int(task_elapsed)),
                         task_eta=secs_to_time(task_eta), counter=counter, total=self.total,
                         pass_progress=pass_progress,
                         pass_elapsed=secs_to_time(int(statistics.get(u'elapsed_time', 0))),
                         pass_eta=secs_to_time(statistics.get(u'eta_time', 0)),
                         pass_fps=statistics.get(u'fps', 0)))
        try:
            if self.api_servers:
                headers = {u'Content-type': u'application/json'}
                data = json.dumps({
                    u'elapsed': task_elapsed, u'eta': task_eta, u'filename': self.filename,
                    u'original_size': self.original_size, u'product_id': self.product_id, u'progress': task_progress,
                    u'publisher_id': self.publisher_id, u'status': state, u'url': url
                })
                for api_server in self.api_servers:
                    requests.post(api_server[u'url'], auth=api_server[u'auth'], headers=headers, data=data)
        except:
            self.logger.exception(u'Unable to report progress')


def send_error_email(exception, filename, settings, subject=u'[EncodeBox] Transcoding task failed'):
    recipients = settings['email_recipients']
    if recipients:
        template = Template(open(settings[u'email_body'], u'r', u'utf-8').read())
        message = template.render(exception=repr(exception), filename=filename, settings=settings)
        return send_email(settings[u'email_host'], settings[u'email_username'], settings[u'email_password'], recipients,
                          subject, message)
