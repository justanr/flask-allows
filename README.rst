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


Why not Flask-Principal?
------------------------

I have nothing against Flask-Principal, I just found that it didn't work for
what I needed without adding an extra layer around it.
