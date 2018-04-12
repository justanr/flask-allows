############
Flask-Allows
############


Flask-Allows gives you the ability to impose identity requirements on routes
in your Flask application::


    from flask import Flask
    from flask_allows import Allows, Requirement
    from flask_login import current_user

    app = Flask(__name__)
    allows = Allows(app=app, identity_loader=lambda: current_user)

    class IsAdmin(Requirement):
        def requires(self, user, request):
            return user.permissions.get('admin')

    @app.route('/admin')
    @allows.requires(IsAdmin())
    def admin_index():
        return "Welcome to the super secret club"


************
Installation
************

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


*******
Content
*******

.. toctree::
   :maxdepth: 2

   quickstart
   requirements
   helpers
   failure
   api

