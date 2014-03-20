# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    The states of a media asset from PENDING to SUCCESS

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from celery import states

ENCODING = u'ENCODING'
TRANSFERRING = u'TRANSFERRING'
TRANSFER_ERROR = u'TRANSFER_ERROR'
FAILURE = states.FAILURE
SUCCESS = states.SUCCESS
STARTED = states.STARTED
