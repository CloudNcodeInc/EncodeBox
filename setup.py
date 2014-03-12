#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Install EncodeBox on the system.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, subprocess, stat, sys, zipfile
from codecs import open
from pip.req import parse_requirements
from setuptools import setup, find_packages

major, minor = sys.version_info[:2]
kwargs = {}
if major >= 3:
    print(u'Converting code to Python 3 helped by 2to3')
    kwargs[u'use_2to3'] = True

# https://pypi.python.org/pypi?%3Aaction=list_classifiers

classifiers = u"""
Development Status :: 2 - Pre-Alpha
Intended Audience :: Developers
License :: Other/Proprietary License
Natural Language :: English
Operating System :: POSIX :: Linux
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
Programming Language :: Python :: Implementation :: CPython
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


def post_install():
    import pwd
    from encodebox import celeryconfig
    from pytoolbox.filesystem import chown, from_template, try_makedirs, try_remove
    from pytoolbox.network.http import download
    user_name = os.getlogin()
    print(u'Install Debian packages')
    packages = filter(None, (p.strip() for p in open(u'requirements.apt')))
    subprocess.check_call([u'apt-get', u'-y', u'install'] + packages)
    print(u'Download and install Nero AAC encoder')
    try:
        download(u'ftp://ftp6.nero.com/tools/NeroDigitalAudio.zip', u'/tmp/nero.zip')
        zipfile.ZipFile(u'/tmp/nero.zip').extract(u'linux/neroAacEnc', u'/usr/local/bin')
        os.chmod(u'/usr/local/bin/neroAacEnc', os.stat(u'/usr/local/bin/neroAacEnc').st_mode | stat.S_IEXEC)
    finally:
        try_remove(u'/tmp/nero.zip')
    print(u'Create directory for storing persistent data')
    try_makedirs(celeryconfig.LIB_DIRECTORY)
    chown(celeryconfig.LIB_DIRECTORY, user_name, pwd.getpwnam(user_name).pw_gid, recursive=True)
    print(u'Register and start our services as user ' + user_name)
    from_template(u'etc/encodebox.conf.template', u'/etc/supervisor/conf.d/encodebox.conf', {
        u'lib_directory': celeryconfig.LIB_DIRECTORY, u'user': user_name
    })
    subprocess.call([u'service', u'supervisor', u'force-reload'])


call_hook(u'pre_' + action)

setup(
    name=u'encodebox',
    version=u'0.4.3-beta',
    packages=find_packages(exclude=[u'tests']),
    description=u'Transcoding watchfolder called EncodeBox',
    long_description=open(u'README.rst', u'r', encoding=u'utf-8').read(),
    author=u'David Fischer',
    author_email=u'david.fischer.ch@gmail.com',
    #url='<TODO address of the repository>',
    license=u'(c) 2014 <TODO Company> Inc. All rights reserved.',
    classifiers=filter(None, classifiers.split(u'\n')),
    keywords=[u'ffmpeg', u'json', u'rsync'],
    include_package_data=True,
    install_requires=[str(requirement.req) for requirement in parse_requirements(u'requirements.txt')],
    data_files=[(u'/etc', [u'etc/encodebox.yaml'])],
    entry_points={u'console_scripts': [u'encodebox=encodebox.daemon:main']},
    tests_require=['coverage', 'mock', 'nose'],
    test_suite=u'tests.encodebox_runtests.main', **kwargs)

call_hook(u'post_' + action)
