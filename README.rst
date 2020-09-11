Supervisor Cron Mod
===================

A modification of supervisor that supports scheduling start/stop/restart 
of the jobs in the config. It adds 3 options, cron_start, cron_stop and 
cron_restart. Each is a cron-like expression. For example, the following 
config will start the job every two minute and stop it every three minutes::

    [program: test]
    command = sleep infinity
    cron_start = */2 * * * *
    cron_stop = */3 * * * *


Supervisor
==========

Supervisor is a client/server system that allows its users to
control a number of processes on UNIX-like operating systems.

Supported Platforms
-------------------

Supervisor has been tested and is known to run on Linux (Ubuntu), Mac OS X
(10.4, 10.5, 10.6), and Solaris (10 for Intel) and FreeBSD 6.1.  It will
likely work fine on most UNIX systems.

Supervisor will not run at all under any version of Windows.

Supervisor is intended to work on Python 3 version 3.4 or later
and on Python 2 version 2.7.

Documentation
-------------

You can view the current Supervisor documentation online `in HTML format
<http://supervisord.org/>`_ .  This is where you should go for detailed
installation and configuration documentation.

Reporting Bugs and Viewing the Source Repository
------------------------------------------------

Please report bugs in the `GitHub issue tracker
<https://github.com/Supervisor/supervisor/issues>`_.

You can view the source repository for supervisor via
`https://github.com/Supervisor/supervisor
<https://github.com/Supervisor/supervisor>`_.

Contributing
------------

We'll review contributions from the community in
`pull requests <https://help.github.com/articles/using-pull-requests>`_
on GitHub.
