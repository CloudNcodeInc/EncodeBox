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

import requests

if __name__ == u'__main__':
    print(requests.get(u'http://127.0.0.1:5000/encoding/report').json())
