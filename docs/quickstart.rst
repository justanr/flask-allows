.. _quickstart_guide:

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


**************************
Guarding entire blueprints
**************************

If you find yourself applying the same set of requirements to every route in
a blueprint, you can instead guard an entire blueprint with that set of
requirements instead using :func:`~flask_allows.views.guard_blueprint`::


    from flask import Blueprint
    from flask_allows import guard_blueprint

    from myapp.requirements import is_admin


    admin_area = Blueprint(__name__, "admin_area")
    admin_area.before_request(guard_blueprint([is_admin]))

You may also specify what happens when the requirements aren't met by providing
either of ``throws`` or ``on_fail``. If ``on_fails`` returns a non-None value,
that will be treated as the result of the routing request::

    from flask import flash, redirect

    def flash_and_redirect(message, level, endpoint):
        def flasher(*a, **k):
            flash(message, level)
            return redirect(endpoint)
        return _

    admin_area.before_request(
        guard_blueprint(
            [is_admin],
            on_fail=flash_and_redirect(
                message="Must be admin",
                level="danger",
                endpoint="index"
            )
        )
    )


``guard_blueprint`` will pass ``flask.request.view_args`` as keyword arguments
to the ``on_fail`` handler registered with it, this is useful is the blueprint
is registered with a dynamic component such as a username::

    def flash_formatted_message(message, level):
        def flasher(*a, **k):
            flash(message.format(**k), level)
        return flasher

    user_area = Blueprint(__name__, "users")
    user_area.before_request(
        guard_blueprint(
            [MustBeLoggedIn()],
            on_fail=flash_formatted_message(
                "Must be logged in to view {}'s profile",
                level="warning"
            )
        )
    )


If you need to exempt a route handler inside the blueprint from these
permissions, that is possible as well by using
:func:`~flask_allows.views.exempt_from_requirements`::

    @admin_area.route('/unpermissioned')
    @exempt_from_requirements
    def index():
        ...


.. danger::

    ``exempt_from_requirements`` only prevents ambient runners like
    ``guard_blueprint`` from acting on the route handler. However, if
    ``requires``, ``allows.requires`` or another runner acts on the route
    then those requirements will be run.
