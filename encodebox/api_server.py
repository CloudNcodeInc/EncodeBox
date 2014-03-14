#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    An example API only for debugging purposes.

    See http://celery.readthedocs.org/en/latest/configuration.html for a list of the available options.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
from flask import Flask, request
from collections import defaultdict
from pytoolbox.network.http import get_request_data

app = Flask(__name__)


reports = defaultdict(lambda: defaultdict(dict))


@app.route(u'/encoding/report/<int:user_id>/<int:content_id>/<name>', methods=[u'POST'])
def receive_encoding_report(user_id, content_id, name):
    data = get_request_data(request, sources=[u'json'])
    reports[user_id][content_id][name] = data
    print(user_id, content_id, name, data)
    return u'Hello World!'


@app.route(u'/encoding/report', methods=[u'GET'])
def send_reports():
    print(u'Send reports {0}'.format(reports))
    return json.dumps(reports)

if __name__ == u'__main__':
    app.run()
