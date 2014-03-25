# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Utility library of the asynchronous tasks started by the Celery worker.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json, requests, time
from pytoolbox.datetime import secs_to_time


class TranscodeProgressReport(object):

    def __init__(self, api_url, api_auth, publisher_id, product_id, filename, original_size, logger):
        self.api_url = api_url
        self.api_auth = api_auth
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

    def send_report(self, state, counter=None, statistics=None):
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
            headers = {u'Content-type': u'application/json'}
            requests.post(self.api_url, auth=self.api_auth, headers=headers, data=json.dumps({
                u'elapsed': task_elapsed, u'eta': task_eta, u'filename': self.filename,
                u'original_size': self.original_size, u'product_id': self.product_id, u'progress': task_progress,
                u'publisher_id': self.publisher_id, u'status': state,
                u'url': u'The-URL-of-a-file-depends-of-the-web-server-cfg-and-the-FQDN.com/something/we/do-not/manage'
            }))
        except:
            self.logger.exception(u'Unable to report progress')
