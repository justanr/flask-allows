.. image:: https://travis-ci.org/justanr/flask-allows.svg?branch=master
    :target: https://travis-ci.org/justanr/flask-allows

.. image:: https://coveralls.io/repos/github/justanr/flask-allows/badge.svg?branch=master
:target: https://coveralls.io/github/justanr/flask-allows?branch=master



flask-allows
============

Are you permissions making too much noise all the time? Are your permissions
stomping all over your actual code? Are your permission decorators clawing
at your line count all the time? Think there's no answer? There is! Flask-Allows.


Flask-Allows is an authorization tool for Flask inspired by
`django-rest-framework <https://github.com/tomchristie/django-rest-framework>`_'s
permissioning system and `rest_condition <https://github.com/caxap/rest_condition>`_'s
ability to compose simple requirements into more complex ones.

Installation
------------

Flask-Allows is available on `pypi <https://pypi.org/project/flask-allows/>`_ and
installable with::

    pip install flask-allows

Flask Allows supports 2.7, and 3.4+. Support for 3.3 was ended in the version
0.3 release.

.. note::

    If you are installing ``flask-allows`` outside of a virtual environment,
    consider installing it with ``pip install --user flask-allows`` rather
    than using sudo or adminstrator privileges to avoid installing it into
    your system Python.


More Information
----------------

- For more information, `please visit the documentation <http://flask-allows.readthedocs.io/en/latest/>`_.
- Found a bug, have a question, or want to request a feature? Here is our `issue tracker <https://github.com/justanr/flask-allows/issues>`_.
- Need the source code? Here is the `repository <https://github.com/justanr/flask-allows>`_
