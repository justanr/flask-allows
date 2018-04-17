############
Flask-Allows
############

Version |version| (:ref:`Change log <changelog>`)

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

.. include:: installation.rst

*******
Content
*******

.. toctree::
   :maxdepth: 1

   quickstart
   requirements
   helpers
   failure
   api
   changelog
