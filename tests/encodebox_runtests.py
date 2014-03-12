#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Run both the unit tests and integration tests of EncodeBox.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""


def main():
    from pytoolbox.encoding import configure_unicode
    from pytoolbox.unittest import runtests
    configure_unicode()
    return runtests(__file__, cover_packages=[u'encodebox'], packages=[u'encodebox'])

if __name__ == u'__main__':
    main()
