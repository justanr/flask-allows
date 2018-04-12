.. _failure:


===================
Controlling Failure
===================


When dealing with permissioning, failure is an expected and desired outcome. And
Flask-Allows provides several measures to deal with this failure.


*********************
Throwing an exception
*********************

The first measure is the ability to configure requirements runners to throw an
exception. By default this will be werkzeug's Forbidden exception. However,
this can be set to be any exception type or specific instance. The easiest
way to set this is through the :class:`~flask_allows.allows.Allows` constructor::

    class PermissionError(Exception):
        def __init__(self):
            super().__init__("I'm sorry Dave, I'm afraid I can't do that")


    allows = Allows(throws=PermissionError)

    # alternatively
    allows = Allows(throws=PermissionError())


If a particular exception is desirable most of but not all of the time, an
exception type or instance can be provided each requirements runner::

    # to Permission helper
    Permission(SomeRequirement(), throws=PermissionError)

    # to decorators
    @allows.requires(SomeRequirement(), throws=PermissionError)
    @requires(SomeRequirement(), throws=PermissionError)


When an exception type or instance is provided to a requirements runner, it
takes precedence over the type or instance registered on the extension object.
If one is not supplied to a requirement runner, it uses the type or instance
registered on the extension object.


****************
Failure Callback
****************

Another way to handle failure is providing an ``on_fail`` argument that will be
invoked when failure happens. The value provided to ``on_fail`` doesn't have to
be a callable, so any value is appropriate. If the value provided is a callable
it should be prepared to accept any arbitrary arguments that were provided when
the requirement runner that was invoked.

To add a failure callback, it can be provided to the
:class:`~flask_allows.allows.Allows` constructor::

    def flash_failure_message(*args, **kwargs):
        flash("I'm sorry Dave, I'm afraid I can't do that", "error")

    allows = Allows(on_fail=flash_failure_message)


If ``on_fails`` return a non-``None`` value, that will be used as the return
value from the requirement runner. However, if a ``None`` is returned from the
callback, then the configured exception is raised instead. In the above example,
since a ``None`` is implicitly returned from the callback, a werkzeug Forbidden
exception would be raised from any requirements runners.

An example of returning a value from the callback would be returning a redirect
to another page::


    def redirect_to_home(*args, **kwargs):
        flash("I'm sorry Dave, I'm afraid I can't do that", "error")
        return redirect(url_for("index"))

However, any value can be returned from this wrapper.

.. note::

    When used with the :class:`~flask_allows.permission.Permission` helper,
    the callback will be invoked with no arguments and the return value isn't
    considered.

.. danger::

    When using ``on_fail`` with route decorators, be sure to return an
    appropriate value for Flask to turn into a response.

Similar to exception configuration, ``on_fail`` can be passed to any requirements
runner::

    # to Permission helper
    Permission(SomeRequirement(), on_fail=flash_failure_message)

    # to decorators
    @allow.requires(SomeRequirement(), on_fail=redirect_to_home)
    @requires(SomeRequirement(), on_fail=redirect_to_home)

When ``on_fail`` is passed to a requirements runner, it takes precedence over
the ``on_fail`` registered on the extension object. If an ``on_fail`` isn't
provided then the one registered on the extension object is used.
