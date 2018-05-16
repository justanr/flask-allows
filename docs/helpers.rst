.. _allows_helpers:


#######
Helpers
#######

In addition to the :class:`~flask_allows.allows.Allows`, there are several
helper classes and functions available.


**********
Permission
**********

:class:`~flask_allows.permission.Permission` enables checking permissions as a
boolean or controlling access to sections of code with a context manager. To
construct a Permission, provide it with a collection of requirements to enforce
and optionally any combination of:

- ``on_fail`` callback
- An exception type or instance with ``throws``
- A specific identity to check against with ``identity``

.. note::

    Using ``Permission`` as a boolean or as a context manager requires
    an active application context.

Once configured, the Permission object can be used as if it were a boolean::

    p = Permission(SomeRequirement())

    if p:
        print("Passed!")
    else:
        print("Failed!")

When using Permission as a boolean, only the requirement checks are run but no
failure handling is run as not entering the conditional block is considered
handling the failure. Not running the failure handling on a failed conditional
check also helps cut down on unexpected side effects.


If you'd like the failure handlers to be run, Permission can also be used as a
context manager::

    p = Permission(SomeRequirement())

    with p:
        print("Passed!")

When used as a context manager, if the requirements provided are not met then
the registered ``on_fail`` callback is run and the registered exception type
is raised.

.. note::

    Permission ignores the result of the callback when used as a context
    manager so the exception type is always raised unless the callback raises
    an exception instead.


********
requires
********

If you're using factory methods to create your Flask application and extensions,
it's often difficult to get ahold of a reference to the allows object. Because
of this, the :func:`~flask_allows.view.requires` helper exists as well. This
is a function that calls the configured allows object when the wrapped function
is invoked::

    @requires(SomeRequirement())
    def random():
        return 4

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


The ``requires`` decorator can also be applied to class based views by either
adding it to the ``decorators`` property::

    class SomeView(View):
        decorators = [requires(SomeRequirement())]

When passed into the decorators property, it will guard the entire view and in
the case of ``MethodView`` apply to every action handler on the view.

You may also apply the decorator to individual methods::

    class SomeView(MethodView):

        @requires(SomeRequirement())
        def get(self):
            return render_template('a_template.html')

In this instance, only the the ``get`` method of the view will be guarded but
all other action handlers will not be.
