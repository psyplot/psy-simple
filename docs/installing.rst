.. _install:

.. highlight:: bash

Installation
============

How to install
--------------

Installation using conda
^^^^^^^^^^^^^^^^^^^^^^^^
We highly recommend to use conda_ for installing psy-simple. After downloading
the installer from anaconda_, you can install psy-simple simply via::

    $ conda install -c conda-forge psy-simple

.. _anaconda: https://www.continuum.io/downloads
.. _conda: http://conda.io/

Installation using pip
^^^^^^^^^^^^^^^^^^^^^^
If you do not want to use conda for managing your python packages, you can also
use the python package manager ``pip`` and install via::

    $ pip install psy-simple

Running the tests
-----------------
First, clone the github_ repository, and install psy-simple and pytest_. Then

- create the reference figures via::

    $ pytest --ref

- run the unittests via::

    $ pytest

.. _pytest: https://pytest.org/latest/contents.html
.. _github: https://github.com/psyplot/psy-simple
