.. _api: http://en.wikipedia.org/wiki/Representational_state_transfer
.. _celery: http://celery.readthedocs.org/en/latest/
.. _concurrency: http://celery.readthedocs.org/en/latest/userguide/concurrency/index.html
.. _ffmpeg: http://www.ffmpeg.org/
.. _pip: https://pypi.python.org/pypi/pip
.. _ppa: http://askubuntu.com/questions/4983/what-are-ppas-and-how-do-i-use-them
.. _post: http://en.wikipedia.org/wiki/POST_(HTTP)
.. _rabbitmq: https://www.rabbitmq.com/
.. _revoke: http://celery.readthedocs.org/en/latest/userguide/workers.html#revoking-tasks
.. _supervisor: http://supervisord.org/
.. _task: http://celery.readthedocs.org/en/latest/userguide/tasks.html
.. _tasks: http://celery.readthedocs.org/en/latest/userguide/tasks.html
.. _uuid: http://en.wikipedia.org/wiki/Universally_unique_identifier
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
2. The workers ``tasks.py``: Detect the quality (SD/HD) of the input file and transcode to multiple output files.

The settings file ``/etc/encodebox.yaml`` of EncodeBox permit to configure the following options:

:inputs_directory: (~/EncodeBox/inputs) You must put the files to transcode here.
:outputs_directory: (~/EncodeBox/outputs) The outputs are saved there, within a sub-directory corresponding to the UUID_ of the task.
:temporary_directory: (~/EncodeBox/temporary) The transcoding workers will save the intermediate files here.
:failed_directory: (~/EncodeBox/failed) The input files are moved there if the transcoding task failed.
:completed_directory: (~/EncodeBox/completed) The input files are moved there if the transcoding task succeeded.
:completed_remote_directory: (ubuntu@127.0.0.1:medias/) This option is not yet used (issue #2)
:hd_transcode_passes: (a long list) The transcoding worker follows this list of passes (calls to encoders) to transcode the HD content.
:sd_transcode_passes: (a long list) The transcoding worker follows this list of passes (calls to encoders) to transcode the SD content.

--------------------
State of the project
--------------------

The project is currently a beta release that implement the complex encoding workflow trigerred for each new file in the
inputs directory. The transcoding worker is now able to parse both the output of FFmpeg_ and x264_ to retrieve the
statistics like *ETA, fps, progress %*, ... It means that we can report a *PROGRESS* status with both the current pass
(e.g. 4 of 14) and the statistics about the current pass.

The "core" available features are:

* The watch-folder daemon react to *IN_CLOSE_WRITE* and launch a new transcoding task_
* The transcoding worker is able to :
    * Detect the resolution of the input media file
    * Select the appropriate transcoding steps (described in the settings file ``/etc/encodebox.yaml``)
    * Execute the transcoding steps and update the status of the task_ to *PROGRESS* + statistics
    * Remove the temporary files
    * Remove the output files in case of error
    * Update the status of the task_ to *SUCCESS* or *FAILURE* + console output of the encoder

The "core" missing features are:

* The cleanup task_ to remove files older than 7 days (issue #1)
* The transcoding worker does not :
   * POST_ to the API_, needs workflow design + tests (issue #12 + #4)
   * Copy the output files to the remote streaming server, needs workflow design + tests (issue #2)
* The watch-folder does not revoke_/relaunch tasks_ if the input files are removed or updated during transcoding (issue #13)
* The settings file does not include the options for Celery_ like concurrency_ (# of parallel worker processes), ... (issue #14)
* The setup script does not configure RabbitMQ_ with a password (issue #9)

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
