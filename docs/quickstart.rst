.. _quickstart:

##########
Quickstart
##########

This guide will walk you through the basics of creating and using requirements
with Flask-Allows.

*****************
Setting Up Allows
*****************

Before we can set up requirements and guard routes, we must first setup the
extension object::

    from flask_allows import Allows
    from flask import Flask

    app = Flask(__name__)

    allows = Allows(app)

This is all that is needed to register the extension object against a Flask
application, however we must also register a way to load a user object to
check against requirements. Managing user sessions is outside the scope of
Flask-Allows, however for the sake of this tutorial we'll assume that you are
using ``flask_login``::

    from flask_login import current_user

    allows.identity_loader(lambda: current_user)

An identity_loader can also being provided at object instantiation::

    Allows(identity_loader=lambda: current_user)

*********************
Creating Requirements
*********************

Now that we have a configured :class:`~flask_allows.allows.Allows` instance
registered against the application, let's create some custom requirements.
Requirements can either be a child of
:class:`~flask_allows.requirements.Requirement`::

    class HasPermission(Requirement):
        def __init__(self, permission):
            self.permission = permission

        def fulfill(self, user):
            return self.permission in user.permissions


or a function that accepts the current identity::

    def is_admin(user):
        return 'admin' in user.groups


.. note::

    Until version 0.5.0 requirements, both class and function based, needed
    to accept both an identity and the current request. This has been
    deprecated in favor of accepting only the identity and will be removed
    in version 1.0.0.


These classes and functions can be as simple or as complicated as needed to
enforce a particular requirement to guard a route or action inside your
application.

***************
Guarding Routes
***************

In order to guard route handlers, two decorators are provided:

- The :meth:`~flask_allows.allows.Allows.requires` method on the configured
  Allows instance
- The standalone :meth:`~flask_allows.views.requires`

Both accept the same arguments the only difference is where each is
imported from. We'll use the standalone decorator in this tutorial.

Applying a requirement is done by passing the desired requirements into the
decorator::

    from flask_allows import requires

    @app.route('/admin')
    @requires(is_admin)
    def admin_section():
        return render_template('admin_section.html')

In order to pass a class based requirement into the decorators, you must pass
an instantiated object rather than the class itself::

    @app.route('/admin')
    @requires(HasPermission('view_admin_panel')
    def admin_section():
        return render_template('admin_section.html')


.. danger::

    If you're using ``requires`` to guard route handlers, the ``route``
    decorator must be applied at the top of the decorator stack (visually first,
    logically last)::

        @app.route('/')
        @requires(SomeRequirement())
        def index():
            pass

    If the ``requires`` decorator comes after the ``route`` decorator, then the
    unguarded function is registered into the application::

        @requires(SomeRequirement())
        @app.route('/')
        def index():
            pass

    This invocation registers the actual ``index`` function into the routing
    map and then decorates the index function.


To apply either of these decorators to class based views, there are two options:

1. Supply it in the ``decorators`` class attribute of the view. In the case of
   ``MethodView`` this will guard every action handler::

    class SomeView(View):
        decorators = [requires(is_admin)]

2. Apply it directly to an action handler, such as with ``MethodView``. In the
   following example, only the ``post`` method will be guarded::

    class SomeView(MethodView):
        def get(self):
            return render_template('some_template.html')

        @requires(is_admin)
        def post(self):
            return render_template('some_tempalte.html')

