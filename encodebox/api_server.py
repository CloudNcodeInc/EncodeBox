#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    An example API only for debugging purposes.

    See http://celery.readthedocs.org/en/latest/configuration.html for a list of the available options.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 CloudNcode Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
from flask import Flask, request
from collections import defaultdict
from pytoolbox.network.http import get_request_data

app = Flask(__name__)


reports = defaultdict(lambda: defaultdict(dict))


@app.route(u'/encoding/report', methods=[u'POST'])
def receive_encoding_report():
    data = get_request_data(request, sources=[u'json'])
    publisher_id = data.pop(u'publisher_id')
    product_id = data.pop(u'product_id')
    filename = data.pop(u'filename')
    reports[publisher_id][product_id][filename] = data
    print(publisher_id, product_id, filename, data)
    return u'Hello World!'


@app.route(u'/encoding/report', methods=[u'GET'])
def send_reports():
    print(u'Send reports containing {0} values'.format(len(reports)))
    return json.dumps(reports)

if __name__ == u'__main__':
    app.run()
