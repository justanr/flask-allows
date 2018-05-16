.. _requirements_guide:


############
Requirements
############


Requirements are how routes and code paths are guarded with Flask-Allows, they
are also entirely defined by the user. Requirements come in two flavors:

- functions
- class based


*********************
Function Requirements
*********************

Function requirements need to accept the current identity and return a boolean
representing if the requirement has been fulfilled or not::

    def user_is_admin(user):
        return user.level == 'admin'

.. note::

    Optionally, the function may accept the request argument, though this
    behavior is deprecated as version 0.5.0 and will be removed in 1.0.0::

        def user_is_admin(user, request):
            return user.level == 'admin'

This function can be provided to any of the requirement runners, if you wanted
to guard a route with it::

    @app.route('/admin')
    @requires(user_is_admin)
    def admin():
        return render_template('admin.html')

Or guard a particular code path with :class:`~flask_allows.permission.Permission`::

    p = Permission(user_is_admin)
    if p:
        print("Welcome!")


************************
Class Based Requirements
************************

Class based requirements are good if you have something to represent that is
too complicated for a function. While it is possible to implement class based
requirements by adding a :meth:`__call__`, there is the
:class:`~flask_allows.requirements.Requirement` that provides the ``fulfill``
hook to implement. It also provides future proofing if new hooks are also
implemented. For example::

    class Has(Requirement):
        def __init__(self, permission):
            self.permission = permission

        def fulfill(self, user):
            return self.permission in user.permissions

.. note::

    Optionally, the fulfill method  may accept the request argument, though
    this behavior is deprecated as version 0.5.0 and will be removed in 1.0.0::


        class Has(Requirement):
            def __init__(self, permission):
                self.permission = permission

            def fulfill(self, user, request):
                return self.permission in user.permissions

To apply this to a route::

    @app.allows('/admin')
    @requires(Has('admin'))
    def admin():
        return render_template('admin.html')

.. danger::

    If you use class based requirements, you are responsible for instantiating
    them and providing any necessary arguments to them. A common mistake is
    providing just the class itself to the requirement runner::

        @app.allows('/admin')
        @requires(Has)
        def admin():
            return render_template('admin.html')

    This will result in an exception being raised at verification because the
    identity and request objects are passed into a constructor that only expected
    one argument. If the constructor expected two arguments, there is a chance
    that the requirement would incorrectly pass as object default to True when
    expressed as booleans.

While using ``Requirement`` isn't strictly necessary, it is provided for people
that prefer an object oriented approach instead.


**********************
Combining Requirements
**********************

In addition to the :class:`~flask_allows.requirements.Requirement` base class,
Flask-Allows also provides a way to combine requirements.

All requirement runners provided by Flask-Allows accept multiple requirements
and all must pass for the verification to pass::


    @app.route('/admin')
    @requires(user_is_logged_in, user_is_admin)
    def admin():
        return render_template('admin.html')

If either requirement returns False, then the user will not be allowed to access
that route. However, if you have a more complicated requirement, such as a
user must be logged in AND a user must be an admin OR a user must have the
``'view_admin_panel'`` permission, these can be difficult to express in an
all-or-nothing evaluation strategy.

To handle these situations, Flask-Allows exposes several helper requirements::


    from flask_allows import And, Or


    @app.route('/admin')
    @requires(And(user_is_logged_in, Or(user_is_admin, Has('view_admin_panel'))))
    def admin():
        return render_template('admin.html')


Strictly speaking, the outer ``And`` isn't necessary as the requirements will
already be combined in an ``and`` fashion but is presented for example sake.
The ``And`` help is most useful when nested inside of an ``Or`` such as::

    Or(user_is_admin, And(Has('view_admin_panel'), user_is_moderator))

Flask-Allows also exposes a helper to invert the result of a requirement::

    @app.route('/login')
    @requires(Not(user_is_logged_in))
    def login():
        return render_template('login.html')

Finally, Flask-Allows also exposes a generalized version of these helpers called
:class:`~flask_allows.requirements.ConditionalRequirement` (also importable as
``C`` to avoid typing out the name every time).


By using ``ConditionalRequirement`` you can build your own requirements combinator.
In addition to the requirements themselves, ``ConditionalRequirement`` will also
accept:

- ``op`` a binary operator to reduce results with
- ``negated`` if the opposite of the result should be returned (e.g. False turns into True)
- ``until`` a boolean value to short circuit on and end evaluation


For example, if you needed your requirements combined with xor, that is possible::

    from operator import xor

    C(perm_1, perm_2, op=xor)


Finally, ``ConditionalRequirement`` also provides the magic methods for:

- ``&`` short cut to applying ``And`` between two instances of ``ConditionalRequirement``
- ``|`` short cut to applying ``Or`` between two instances of ``ConditionalRequirement``
- ``~`` (invert) short to negating a single instance of ``ConditionalRequirement``

Using these operators, our earlier combined and negated requirements would look like::

    C(user_is_logged_in) & (C(user_is_admin) | C(Has('view_admin_panel')))
    ~C(user_is_logged_in)

However, using the named helper methods are often clearer and more efficient.


************************************
Transition to User Only Requirements
************************************

As of version 0.5, passing the request object directly into a requirement is
deprecated and will be removed in version 1.0. Considering the following
requirement::

    from flask_allows import Requirement

    class AllowedToViewPost(Requirement):
        def fulfill(self, user, request):
            post_id = request.view_args.get('post_id')
            if post_id is None:
                abort(404)

            if post.hidden:
                return 'view_hidden_post' in user.permissions

            return True


In order to make the transition to a user only requirement, the only change to
make is::

    from flask import request
    from flask_allows import Requirement

    class AllowedToViewPost(Requirement):
        def fulfill(self, user):
            post_id = request.view_args.get('post_id')
            if post_id is None:
                abort(404)

            if post.hidden:
                return 'view_hidden_post' in user.permissions

            return True

To be clear, ``request`` is now being imported directly from the ``flask``
package. This is the same request object that Allows would pass into the
requirement itself. And the other change is removing the request parameter
from the ``fulfill`` definition.

Behind the scenes, Allows handles both definitions and will dispatch between
them as needed.

.. danger::

    If you have a requirement defined with an optional request, such as::

        def allowed_to_view_post(user, request=None):
            ...

    Allows will incorrectly determine that you have provided a user only
    requirement.

    If your requirement does not need the request object, the
    only change to make is to remove the parameter. If your requirement does
    need the request object you may either remove the default value and Allows
    will determine that you have provided a user-request requirement, or you
    may remove the parameter altogether and import ``request`` directly from
    Flask.

    Additionally, there is :meth:`~flask_allows.requirements.wants_request`
    which marks the requirement as user only but passes the current request
    behind the scenes. This decorator is intended only to assist during a
    transitionary phase and will be remove in flask-allows 1.0
