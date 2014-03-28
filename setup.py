#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Install EncodeBox on the system.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 CloudNcode Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, pwd, stat, sys, zipfile
from codecs import open
from os.path import exists
from pip.req import parse_requirements
from setuptools import setup, find_packages
from subprocess import call, check_call

major, minor = sys.version_info[:2]
kwargs = {}
if major >= 3:
    print(u'Converting code to Python 3 helped by 2to3')
    kwargs[u'use_2to3'] = True
    raise NotImplementedError(u'EncodeBox does not officially supports Python 3.')

# https://pypi.python.org/pypi?%3Aaction=list_classifiers

classifiers = u"""
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: Other/Proprietary License
Natural Language :: English
Operating System :: POSIX :: Linux
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: Implementation :: CPython
Topic :: Adaptive Technologies
Topic :: Multimedia :: Sound/Audio :: Conversion
"""

action = sys.argv[1] if len(sys.argv) > 1 else None


def root_required(error_message=u'This script must be run as root.'):
    u"""Raise an exception if the current user is not root."""
    if not os.geteuid() == 0:
        raise RuntimeError(error_message)


def call_hook(name):
    u"""Call the method by ``name`` only if it does exist."""
    try:
        method = globals()[name]
    except KeyError:
        return
    method()


def pre_install():
    root_required()
    print(u'Install Debian packages')
    packages = filter(None, (p.strip() for p in open(u'requirements.apt')))
    check_call([u'apt-get', u'-y', u'install'] + packages)


def post_install():
    from encodebox import lib
    from pytoolbox.console import confirm
    from pytoolbox.encoding import to_bytes
    from pytoolbox.filesystem import chown, from_template, try_makedirs, try_remove
    from pytoolbox.network.http import download

    if not exists(u'/usr/local/bin/neroAacEnc'):
        try:
            print(u'Download and install Nero AAC encoder')
            download(u'ftp://ftp6.nero.com/tools/NeroDigitalAudio.zip', u'/tmp/nero.zip')
            zipfile.ZipFile(u'/tmp/nero.zip').extract(u'linux/neroAacEnc', u'/usr/local/bin')
            os.chmod(u'/usr/local/bin/neroAacEnc', os.stat(u'/usr/local/bin/neroAacEnc').st_mode | stat.S_IEXEC)
        finally:
            try_remove(u'/tmp/nero.zip')

    filename = lib.SETTINGS_FILENAME
    settings = lib.load_settings(u'etc/config.yaml')
    if not exists(filename) or confirm(u'Overwrite existing configuration file "{0}"'.format(filename)):
        print(u'Generate configuration file "{0}"'.format(filename))
        password = lib.generate_password()
        settings[u'rabbit_password'] = password
        lib.save_settings(filename, settings)

    print(u'Configure RabbitMQ Message Broker')
    check_call([u'service', u'rabbitmq-server', u'start'])
    call([u'rabbitmqctl', u'add_vhost', u'/'])
    call([u'rabbitmqctl', u'delete_user', u'guest'])
    call([u'rabbitmqctl', u'delete_user', u'encodebox'])
    call([u'rabbitmqctl', u'add_user', u'encodebox', settings[u'rabbit_password']])
    check_call([u'rabbitmqctl', u'set_permissions', u'-p', u'/', u'encodebox', u'.*', u'.*', u'.*'])
    users, vhosts = lib.rabbit_users(), lib.rabbit_vhosts()
    print(u'RabbitMQ users: {0} vhosts: {1}'.format(users, vhosts))
    if u'guest' in users or u'encodebox' not in users:
        raise RuntimeError(to_bytes(u'Unable to configure RabbitMQ'))

    print(u'Create directory for storing persistent data')
    try_makedirs(lib.LIB_DIRECTORY)
    chown(lib.LIB_DIRECTORY, lib.USERNAME, pwd.getpwnam(lib.USERNAME).pw_gid, recursive=True)
    print(u'Register and start our services as user ' + lib.USERNAME)
    from_template(u'etc/encodebox.conf.template', u'/etc/supervisor/conf.d/encodebox.conf', {
        u'lib_directory': lib.LIB_DIRECTORY, u'user': lib.USERNAME
    })
    call([u'service', u'supervisor', u'force-reload'])


def pre_livetest():
    from tests import encodebox_livetests
    encodebox_livetests.main()
    sys.exit(0)


call_hook(u'pre_' + action)

setup(
    name=u'encodebox',
    version=u'0.8.0-beta',
    packages=find_packages(exclude=[u'tests']),
    description=u'Transcoding watchfolder called EncodeBox',
    long_description=open(u'README.rst', u'r', encoding=u'utf-8').read(),
    author=u'David Fischer @ CloudNcode Inc.',
    author_email=u'david.fischer.ch@gmail.com',
    url='https://bitbucket.org/cloudncode/encodebox',
    license=u'(c) 2014 CloudNcode Inc. All rights reserved.',
    classifiers=filter(None, classifiers.split(u'\n')),
    keywords=[u'ffmpeg', u'json', u'rsync'],
    include_package_data=True,
    install_requires=[str(requirement.req) for requirement in parse_requirements(u'requirements.txt')],
    data_files=[(u'/etc/encodebox', [u'etc/hd.smil', u'etc/sd.smil'])],
    entry_points={u'console_scripts': [u'encodebox=encodebox.daemon:main']},
    tests_require=['coverage', 'mock', 'nose'],
    test_suite=u'tests.encodebox_runtests.main', **kwargs)

call_hook(u'post_' + action)
