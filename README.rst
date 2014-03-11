.. _supervisor: http://supervisord.org/

=================================
EncodeBox Transcoding Watchfolder
=================================

-----
About
-----

EncodeBox is aimed by the goal of providing a watch-folder that transcode the input media files to various output
formats (adaptive streaming). The outputs are sent to a streaming server for streaming from Wowza.

EncodeBox is, at time of writing this, composed of two services controlled by supervisor_:

1. The watch-folder ``daemon.py``: Launch a new transcoding task for each new file in the input folder.
2. The workers ``tasks.py``: Detect the quality (SD/HD) of the input file and transcode to multiple output files.

--------------------
State of the project
--------------------

The project is currently a beta release that implement the complex encoding workflow trigerred for each new file in the
inputs directory. The transcoding worker is now able to parse both the output of ffmpeg and x264 to retrieve the
statistics like ETA, fps, progress %, ... It means that we can report a PROGRESS status with both the current pass (e.g.
4 of 14) and the statistics about the current pass.

The "core" available features are:

* The watch-folder daemon react to IN_CLOSE_WRITE and launch a new transcoding task
* The transcoding worker is able to :
    * Detect the resolution of the input media file
    * Select the appropriate transcoding steps (described in the settings file)
    * Execute the transcoding steps and update the status of the task to PROGRESS + statistics
    * Remove the temporary files
    * Remove the output files in case of error
    * Update the status of the task to SUCCESS or FAILURE + console output of the encoder

The "core" missing features are:

* The cleanup task to remove files older than 7 days (see #1)
* The transcoding worker does not :
   * POST to the API, needs workflow design + tests (see #12 + #4)
   * Copy the output files to the remote streaming server, needs workflow design + tests (see #2)
* The watch-folder does not revoke/relaunch tasks if the input files are removed or updated during transcoding (see #13)
* The settings file does not include the options for celery like concurrency (# of parallel worker processes), ... (see #14)
* The setup script does not configure RabbitMQ with a password (see #9)

------------------------------------
What the release number stands for ?
------------------------------------

I do my best to follow this interesting recommendation : `Semantic Versioning 2.0.0 <http://semver.org/>`_

-------------------
How to install it ?
-------------------

Add the following PPA if you want to install the **real** ffmpeg::

    sudo apt-add-repository ppa:jon-severinsson/ffmpeg
    sudo apt-get update

Make sure that pip is up-to-date (PIPception)::

    sudo pip install --upgrade pip

Then, you only need to run ``setup.py``::

    python setup.py test
    sudo python setup.py install

---------------
How to use it ?
---------------

Manage the services::

    sudo service supervisor {start|stop|restart|force-reload|status|force-stop}
    sudo supervisorctl
    > status
    > restart
    > ...

Follow the logs::

    tail -f /var/log/encodebox-*.log
