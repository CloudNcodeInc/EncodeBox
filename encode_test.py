#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Transcoding watchfolder called EncodeBox
# Retrieved from git clone https://bitbucket.org/cloudncode/encodebox.git
u"""
    Test the transcoding steps.

    :author: David Fischer <david.fischer.ch@gmail.com>
    :copyright: (c) 2014 <TODO Company> Inc. All rights reserved.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import glob, os, shlex, shutil, sys, uuid
from pytoolbox.filesystem import try_makedirs
from subprocess import check_call

template_steps = (
    u'ffmpeg -analyzeduration 2147480000 -i "{input}" -ar 48000 -ac 2 -y "{tmp}a.wav"',
    u'neroAacEnc -cbr 128000 -lc -if "{tmp}a.wav" -of "{tmp}a.mp4"',

    u'ffmpeg -i "{input}" -r 25 -s 854x480 -aspect 16:9 -f yuv4mpegpipe -pix_fmt yuv420p -vsync 1 -g 100 '
    u'-keyint_min 100 -movflags frag_keyframe -y "{tmp}v.y4m"',

    u'x264 --pass 1 --fps 25 --bitrate 2000 --no-scenecut --stats "{tmp}x264pass.log" -o /dev/null "{tmp}v.y4m"',
    u'x264 --pass 2 --fps 25 --bitrate 2000 --no-scenecut --stats "{tmp}x264pass.log" -o "{tmp}v.h264" "{tmp}v.y4m"',
    u'ffmpeg -i "{tmp}v.h264" -i "{tmp}a.mp4" -vcodec copy -acodec copy -y "{out}{name}_2000.mp4"',

    u'ffmpeg -i "{input}" -r 25 -s 480x272 -aspect 16:9 -f yuv4mpegpipe -pix_fmt yuv420p -vsync 1 -g 100 '
    u'-keyint_min 100 -movflags frag_keyframe -y "{tmp}v.y4m"',
    u'x264 --pass 1 --fps 25 --bitrate 894 --no-scenecut --stats "{tmp}x264pass.log" -o /dev/null "{tmp}v.y4m"',
    u'x264 --pass 2 --fps 25 --bitrate 894 --no-scenecut --stats "{tmp}x264pass.log" -o "{tmp}v.h264" "{tmp}v.y4m"',
    u'ffmpeg -i "{tmp}v.h264" -vcodec copy -y "{out}{name}_894.mp4"',

    u'ffmpeg -i "{input}" -r 25 -s 288x160 -aspect 16:9 -f yuv4mpegpipe -pix_fmt yuv420p -vsync 1 -g 100 '
    u'-keyint_min 100 -movflags frag_keyframe -y "{tmp}v.y4m"',
    u'x264 --pass 1 --fps 25 --bitrate 400 --no-scenecut --stats "{tmp}x264pass.log" -o /dev/null "{tmp}v.y4m"',
    u'x264 --pass 2 --fps 25 --bitrate 400 --no-scenecut --stats "{tmp}x264pass.log" -o "{tmp}v.h264" "{tmp}v.y4m"',
    u'ffmpeg -i "{tmp}v.h264" -vcodec copy -y "{out}{name}_400.mp4"',
)

task_id = unicode(uuid.uuid4())  # This simulate the task ID of a celery task

options = {
    u'name': os.path.splitext(os.path.basename(sys.argv[1]))[0],
    u'input': sys.argv[1],
    u'out': u'outputs' + os.sep + task_id + os.sep,   # The outputs directory
    u'tmp': u'temporary' + os.sep + task_id + os.sep  # The temporary directory
}

try:
    try_makedirs(options[u'out'])
    try_makedirs(options[u'tmp'])
    steps = [shlex.split(s.format(**options)) for s in template_steps]
    for step in steps:
        print(u'Execute ' + u' '.join(step))
        check_call(step)
except:
    # Remove the output files in case of error
    for f in glob.glob(options[u'out'] + options[u'name'] + '*'):
        os.remove(f)
finally:
    # Remove the temporary files
    shutil.rmtree(options[u'tmp'], ignore_errors=False)
