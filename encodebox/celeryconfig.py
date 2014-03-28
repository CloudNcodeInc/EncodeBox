# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Configuration module of the workers.

    See http://celery.readthedocs.org/en/latest/configuration.html for a list of the available options.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 CloudNcode Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from . import lib

# Time and date settings (http://celery.readthedocs.org/en/latest/configuration.html#id6)

CELERY_ENABLE_UTC = True

# Task result backend settings (http://celery.readthedocs.org/en/latest/configuration.html#id9)

# Using the database to store task state and results.
CELERY_RESULT_BACKEND = u'db+sqlite://' + lib.LIB_DIRECTORY + u'/database.sqlite'
CELERY_RESULT_SERIALIZER = u'json'
CELERY_RESULT_PERSISTENT = True

# Broker settings (http://celery.readthedocs.org/en/latest/configuration.html#id19)

CELERY_ACCEPT_CONTENT = [u'json']

BROKER_URL = u'amqp://encodebox:{rabbit_password}@localhost//'.format(**lib.load_settings())

# Task execution settings (http://celery.readthedocs.org/en/latest/configuration.html#id20)

CELERY_MESSAGE_COMPRESSION = u'bzip2'
CELERY_TRACK_STARTED = True
CELERY_TASK_SERIALIZER = u'json'

# Error e-mails settings (http://celery.readthedocs.org/en/latest/configuration.html#id22)
# Logging settings (http://celery.readthedocs.org/en/latest/configuration.html#id25)
# Security settings (http://celery.readthedocs.org/en/latest/configuration.html#id26)

# Periodic task server settings (http://celery.readthedocs.org/en/latest/configuration.html#id28)

from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    u'cleanup-every-10-minutes': {
        u'task': 'encodebox.tasks.cleanup',
        u'schedule': timedelta(minutes=10)
    },
}
