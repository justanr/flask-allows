.. image:: https://travis-ci.org/justanr/flask-allows.svg?branch=master
    :target: https://travis-ci.org/justanr/flask-allows


flask-allows
============

Are you permissions making too much noise all the time? Are your permissions
stomping all over your actual code? Are your permission decorators clawing
at your line count all the time? Think there's no answer? There is! Flask-Allows.


Flask-Allows is an authorization tool for Flask inspired by
`django-rest-framework <https://github.com/tomchristie/django-rest-framework>`_'s
permissioning system and `rest_condition <https://github.com/caxap/rest_condition>`_'s
ability to compose simple requirements into more complex ones.

Install
-------

Just yer standard `pip install flask-allows`

Flask Allows supports 2.7, and 3.4+. Support for 3.3 was ended in the version 0.3 release


Quickstart
----------

Flask-Allows provides a simple route decorator that accepts a list of requirements,
which can be any callable that accept an identity and the current request.

.. code:: Python

    from flask_allows import Allows
    from flask import g, request
    from .myapp import app

    allows = Allows(identity_loader=lambda: g.user)

    def is_staff(ident, request):
        return ident.permlevel == 'staff'

    @app.route('/staff_only')
    @allows.requires(is_staff)
    def staff_only():
        return "Welcome to the staff lounge"

Flask-Allows also provides a Permission class that can act as either a boolean
or a context manager. This depends on flask-allows being previously configured
on the current application.


.. code:: Python

    from flask import render_template
    from flask_allows import Permission
    from .myapp import app
    from .requirements import is_staff

    @app.route('/')
    def index():
        if Permission(is_staff):
            return render_template('staff_index.html')
        else:
            return render_template('user_index.html')

    @app.route('/do_stuff')
    def do_stuff():
        with Permission(is_staff):
            do_staff_stuff()

When using `Permission` as a context manager, if the loaded identity doesn't
meet the requirements, an exception is thrown immediately. However, when used
as a boolean, it simply returns True or False.


It's also possible to provide an already loaded user to `Permission` by passing
it via the `identity` keyword.


More Advanced Stuff
------------------

flask-allows provides a small toolkit for crafting more complex requirements.
One of these is the base `Requirement` class:

.. code:: Python

    from flask_allows import Requirement
    from .models import Forum, Group

    class CanAccessForum(Requirement):
        def fulfill(self, identity, request):
            forum_id = self.determine_forum_id(request)
            user_group_ids = self.get_user_group_ids(user)

            q = Forum.query.with_entities(Forum.id).filter(
                Forum.id == forum_id, Forum.groups.any(Group.id.in_(user_group_ids))
                ).first()

            return q is not None

        def determine_forum(self, request):
            # do something complicated to determine the forum_id
            return request.view_args['forum_id']

        def user_group_ids(self, user):
            if user.is_anonymous():
                return [Group.get_guest_group().id]
            else:
                return [gr.id for gr in user.groups]

When providing a class based requirement to be fulfilled, you must
instantiate it in case there's any setup that needs to be performed.

.. code:: Python

    #wrong!
    @allows.requires(CanAccessForum)
    def forum(forum_id):
        ...

    #right
    @allows.requires(CanAccessForum())
    def forum(forum_id):
        ...

Or if you have many simple requirements that need to be composed into a more
complex requirement, this is provided as well:

.. code:: Python

    from flask_allows import And, Or Not
    from .requirements import is_staff, read_only, is_member

    @allows.requires(Or(is_staff, And(readonly, is_member)))
    def something():
        ...


Applying To Class Based View
----------------------------

Adding permissions to your class based views (CBV) is easy, just include either the
`allows.requires` or `requires` decorator in the `decorators` attribute of the CBV:

.. code:: Python

    from flask.views import View
    from flask_allows.views import requires
    from .requirements import MyRequirement


    class SomeCBV(View):
        decorators = [requires(MyRequirement())

        def dispatch_request(self):
            ...


Alternatively, if you have a method view, and only need to apply permissions to some of the
methods, you can decorator those methods only:


.. code:: Python

    class SomeMethodView(MethodView):

        def get(self):
            pass

        @requires(MyRequirement())
        def post(self):
            ...


Get requests won't trigger the permission checking, but posts will.


Controlling Failure
-------------------

When used as a decorator or context manager, Allows will raise werkzeug's Forbidden exception
by default. However, this exception can be configured to any exception you want:

.. code:: Python

    class MyForbidden(Exception):
        pass

    # Either at extension creation
    allows = Allows(throws=MyForbidden)

    # At decoration
    # also applies to flask_allows.views.requires
    @allows.requires(MyRequirement(), throws=MyForbidden)
    def stub():
        pass

    # Or with Permission
    perm = Permission(MyRequirement(), throws=MyForbidden)


Additionally, an `on_fail` value may be passed. When used with decoration, this value will be
returned instead of raising an exception. If a function is passed, then it will receive the
arguments passed to the route handler as well, and if a value is returned from the function,
it will be returned to the caller instead of raising an exception.

When used with `Permission`, `on_fail` will be called with no arguments and is only invoked when
used as a context manager. This can be used to flash a message or record bad behavior, but not
intercept the raised exception.


.. code:: Python

    # plain value, will be returned
    Allows(on_fail="Uh oh, you're not allowed to do that")

    # propagate return from function
    Allows(on_fail=lambda *a, **k: "Someones been clicking the wrong links")

    # no value returned, exception will be raised
    Allows(on_fail=lambda *a, **k: flash("Don't do that"))


`on_fail` may also be passed to any of `allows.requires`, `flask_allows.views.requires`, or
`Permission`, in these cases this will take precedence over the `on_fail` configured on the
`Allows` instance.


Why not Flask-Principal?
------------------------

I have nothing against Flask-Principal, I just found that it didn't work for
what I needed without adding an extra layer around it.
