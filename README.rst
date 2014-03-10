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

------------------------------------
What the release number stands for ?
------------------------------------

I do my best to follow this interesting recommendation : `Semantic Versioning 2.0.0 <http://semver.org/>`_

-------------------
How to install it ?
-------------------

Install some packages that are not handled by pip::

    sudo apt-add-repository ppa:jon-severinsson/ffmpeg
    sudo apt-get update
    sudo apt-get install ffmpeg libyaml-dev libxml2-dev libxslt-dev libz-dev python-dev python-pip supervisor

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
