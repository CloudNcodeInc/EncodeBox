.. _api: http://en.wikipedia.org/wiki/Representational_state_transfer
.. _celery: http://celery.readthedocs.org/en/latest/
.. _concurrency: http://celery.readthedocs.org/en/latest/userguide/concurrency/index.html
.. _ffmpeg: http://www.ffmpeg.org/
.. _flower: https://github.com/mher/flower
.. _smil: http://en.wikipedia.org/wiki/Synchronized_Multimedia_Integration_Language
.. _pip: https://pypi.python.org/pypi/pip
.. _ppa: http://askubuntu.com/questions/4983/what-are-ppas-and-how-do-i-use-them
.. _post: http://en.wikipedia.org/wiki/POST_(HTTP)
.. _rabbitmq: https://www.rabbitmq.com/
.. _revoke: http://celery.readthedocs.org/en/latest/userguide/workers.html#revoking-tasks
.. _rsync: http://rsync.samba.org/
.. _smtp: http://fr.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol
.. _supervisor: http://supervisord.org/
.. _task: http://celery.readthedocs.org/en/latest/userguide/tasks.html
.. _tasks: http://celery.readthedocs.org/en/latest/userguide/tasks.html
.. _url: http://en.wikipedia.org/wiki/Uniform_Resource_Locator
.. _uuid: http://en.wikipedia.org/wiki/Universally_unique_identifier
.. _watch: http://en.wikipedia.org/wiki/Watch_(Unix)
.. _worker: http://docs.celeryproject.org/en/latest/userguide/workers.html
.. _workers: http://docs.celeryproject.org/en/latest/userguide/workers.html
.. _wowza: http://www.wowza.com/
.. _x264: http://www.videolan.org/developers/x264.html

=================================
EncodeBox Transcoding Watchfolder
=================================

-----
About
-----

EncodeBox is aimed by the goal of providing a watch-folder that transcode the input media files to various output
formats (adaptive streaming). The outputs are sent to a streaming server for streaming from Wowza_.

EncodeBox is, at time of writing this, composed of two services controlled by supervisor_:

1. The watch-folder ``daemon.py``: Launch a new transcoding task_ for each new file in the input folder.
2. The workers_ ``tasks.py``: Detect the quality (SD/HD) of the input file and transcode to multiple output files.

The settings file ``/etc/encodebox/config.yaml`` of EncodeBox permit to configure the following options:

:filenames_seed: (filenames_seed) The seed for the function generating unguessable filenames.
:local_directory: (/var/www/data) All the files managed by EncodeBox must be transfered there.
:remote_directory: (username@host_ip:/usr/local/WowzaStreamingEngine/content) The outputs are copied to this directory with rsync_. Can be remote or local.
:remote_url: (http://host_ip:1935/vod/content/{publisher_id}/{product_id}/smil:{name}.smil/Manifest) The Wowza player use this kind of URL, so here is the template.
:completed_cleanup_delay: (604800) Completed files are removed if older than this delay in seconds, default means 7 days.
:api_url: (http://127.0.0.1:5000/encoding/report) Socket to POST (API) the progress reports of the transcoding tasks.
:api_auth: (null) Credentials to POST (API) the progress report.
:email_body: (/etc/encodebox/email_body.j2) The template used to generate the body of the error report.
:email_host: (smtp.gmail.com) The SMTP_ host to send the e-mail messages.
:email_username: (encodebox.test@gmail.com) The username of the mailbox used to send the e-mail messages.
:email_password: (1**************e) The password of the mailbox used to send the e-mail messages.
:email_recipients: (['aaron@sigalamedia.com', 'david.fischer.ch@gmail.com']) Recipients for the error reports. Set to null to disable this feature.
:hd_smil_template: (/etc/encodebox/hd.smil) The absolute path to the template SMIL_ file for the HD content.
:sd_smil_template: (/etc/encodebox/sd.smil) The absolute path to the template SMIL_ file for the SD content.
:hd_transcode_passes: (a long list) The worker_ follows this list of passes (calls to encoders) to transcode the HD content.
:sd_transcode_passes: (a long list) The worker_ follows this list of passes (calls to encoders) to transcode the SD content.

The transcoding workers_ will handle any input file into ``local_directory/user_id/product_id/uploaded/`` by using the following structure:

* The intermediate files are temporarily stored into the sub-directory ``<local_directory>/user_id/product_id/temporary/``.
* The outputs are saved into the sub-directory ``<local_directory>/user_id/product_id/outputs/``.
* The input file is moved into ``<local_directory>/user_id/product_id/completed/`` in case of success.
* The input file is moved into ``<local_directory>/user_id/product_id/failed/`` in case of failure.

The transcoding workers_ will (try) to POST_ the following informations at the URL_ ``api_url``:

    {
        "publisher_id": "5",
        "product_id": "7",
        "filename": "Abyss.mkv",
        "original_size": 473005964,
        "state": "ENCODING",
        "progress": 0.67316,
        "elapsed": 415.329475,
        "eta": 135,
        "url": null
    }

**Remark**: The ``url`` key is set to the URL_ ``remote_url`` **only** if the task succeeded, when the media asset is
available for streaming.

Following this state-machine:

.. figure:: https://bytebucket.org/cloudncode/encodebox/raw/eb1226392c3c07916cc3ba7dc36cc058291e39d8/docs/state_media.png?token=8180837e4a2e83c23cebb310943326074165a761
    :width: 437px
    :align: center
    :alt: The state-machine of a media asset handled by EncodeBox.

    The state-machine of a media asset handled by EncodeBox.

--------------------
State of the project
--------------------

This project is currently a beta release that implement the complex encoding workflow trigerred for each new file in the
inputs directory. The transcoding worker_ is now able to parse both the output of FFmpeg_ and x264_ to retrieve the
statistics like *ETA, fps, progress %*, ... It means that we can report a *PROGRESS* status with both the current pass
(e.g. 4 of 14) and the statistics about the current pass.

The "core" available features are:

* The watch-folder daemon react to *IN_CLOSE_WRITE* and launch a new transcoding task_
* The transcoding worker_ is able to :
    * Detect the resolution of the input media file
    * Select the appropriate transcoding steps (described in the settings file ``/etc/encodebox/config.yaml``)
    * Execute the transcoding steps and update the status of the task_ to *ENCODING* + statistics
    * Generate the SMIL_ file according to a template
    * Remove the temporary files
    * Remove the output files in case of error
    * Update the status of the task_ to *SUCCESS* or *FAILURE* + console output of the encoder
    * POST_ the progress reports to the API_ during the whole transcoding process
    * Copy the output files to the remote streaming server
* The periodic cleanup task_ remove completed files older than 7 days

Some "extra" are also available to help developers:

* The test API_ server to collect progress of the transcoding tasks_ for debugging purposes.
* The test API_ client reporting the progress of the transcoding tasks_ by calling the test API_ server.

Some "core" features are also not yet implemented:

* The watch-folder does not revoke_/relaunch tasks_ if the input files are removed or updated during transcoding (issue #13)

------------------------------------
What the release number stands for ?
------------------------------------

I do my best to follow this interesting recommendation : `Semantic Versioning 2.0.0 <http://semver.org/>`_

-------------------
How to install it ?
-------------------

Add the following PPA_ if you want to install the **real** FFmpeg_::

    sudo apt-add-repository ppa:jon-severinsson/ffmpeg
    sudo apt-get update

Make sure that pip_ is up-to-date (PIPception)::

    sudo pip install --upgrade pip

Then, you only need to run ``setup.py``::

    python setup.py test
    sudo python setup.py install

You may also install the optional Celery_ web interface (Flower_)::

    sudo pip install flower

---------------------
How to configure it ?
---------------------

* The main configuration file is ``/etc/encodebox/config.yaml``.
* The template SMIL_ files are ``/etc/encodebox/{sd.smil,hd.smil}``.
* The workers_ configuration file is ``celeryconfig.py``.
* The services are registered in ``/etc/supervisor/encodebox.conf``.

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

Watch the watch-folder directories::

    watch ls -lh ~/EncodeBox/*/*/*

Start the optional Celery_ web interface (Flower_)::

    celery flower &
    xdg-open http://localhost:5555

Start the optional test API server::

    screen -dmS api_server python -m encodebox.api_server

Use the test API client to get progress of the transcoding tasks_::

    watch python -m encodebox.api_client

A typical testing scenario:

1. Install, start EncodeBox and open two terminals, one to follow the logs, the other to monitor directories.
2. [optional] Install, start Flower_ and open a browser to monitor transcoding tasks_ and workers_.
3. Start the test API_ server.
4. Copy some media files into the inputs directory ``~/EncodeBox/inputs`` to trigger some new transcoding tasks.
5. Call the test API_ client few times or use watch_ to call it in a regular basis.
