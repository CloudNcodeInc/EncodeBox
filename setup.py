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

import os, subprocess, sys
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
    print(u'Install Debian packages')
    packages = filter(None, (p.strip() for p in open(u'requirements.apt')))
    subprocess.check_call([u'apt-get', u'install'] + packages)
    print(u"Register EncodeBox's services")
    subprocess.check_call([u'supervisorctl', u'reread'])
    subprocess.check_call([u'supervisorctl', u'update'])


call_hook(u'pre_' + action)

setup(
    name=u'encodebox',
    version=u'0.2.2-alpha',
    packages=find_packages(),
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
    data_files=[
        (u'/etc', [u'etc/encodebox.yaml']),
        (u'/etc/supervisor/conf.d', [u'etc/encodebox.conf'])
    ],
    entry_points={u'console_scripts': [u'encodebox=encodebox.daemon:main']},
    **kwargs
)

call_hook(u'post_' + action)
