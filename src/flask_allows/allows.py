import warnings
from functools import wraps

from flask import current_app, request
from werkzeug import LocalProxy
from werkzeug.exceptions import Forbidden

from .overrides import Override, OverrideManager


class Allows(object):
    """
    The Flask-Allows extension object used to control defaults and drive
    behavior.

    :param app: Optional. Flask application instance.
    :param identity_loader: Optional. Callable that will load the current user
    :param throws: Optional. Exception type to raise by default when
        authorization fails.
    :param on_fail: Optional. A value to return or function to call when
        authorization fails.
    """

    def __init__(self, app=None, identity_loader=None, throws=Forbidden, on_fail=None):
        self._identity_loader = identity_loader
        self.throws = throws

        self.on_fail = _make_callable(on_fail)
        self.overrides = OverrideManager()

        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Initializes the Flask-Allows object against the provided application
        """
        if not hasattr(app, "extensions"):  # pragma: no cover
            app.extensions = {}
        app.extensions["allows"] = self

        @app.before_request
        def start_context(*a, **k):
            self.overrides.push(Override())

        @app.after_request
        def cleanup(*a, **k):
            self.clear_all_overrides()

    def requires(self, *requirements, **opts):
        """
        Decorator to enforce requirements on routes

        :param requirements: Collection of requirements to impose on view
        :param throws: Optional, keyword only. Exception to throw for this
            route, if provided it takes precedence over the exception stored
            on the instance
        :param on_fail: Optional, keyword only. Value or function to use as
            the on_fail for this route, takes precedence over the on_fail
            configured on the instance.
        """

        def raiser():
            raise opts.get("throws", self.throws)

        def fail(*args, **kwargs):
            f = _make_callable(opts.get("on_fail", self.on_fail))
            res = f(*args, **kwargs)

            if res is not None:
                return res

            raiser()

        def decorator(f):

            @wraps(f)
            def allower(*args, **kwargs):
                if self.fulfill(requirements):
                    return f(*args, **kwargs)
                else:
                    return fail(*args, **kwargs)

            return allower

        return decorator

    def identity_loader(self, f):
        """
        Used to provide an identity loader after initialization of the
        extension.

        Can be used as a method::

            allows.identity_loader(lambda: a_user)

        Or as a decorator::

            @allows.identity_loader
            def load_user():
                return a_user


        If an identity loader is provided at initialization, this method
        will overwrite it.

        :param f: Callable to load the current user
        """
        self._identity_loader = f
        return f

    def fulfill(self, requirements, identity=None):
        """
        Checks that the provided or current identity meets each requirement
        passed to this method.

        :param requirements: The requirements to check the identity against.
        :param identity: Optional. Identity to use in place of the current
            identity.
        """
        identity = identity or self._identity_loader()

        if self.overrides.current is not None:
            requirements = (r for r in requirements if r not in self.overrides.current)

        return all(_call_requirement(r, identity, request) for r in requirements)

    def clear_all_overrides(self):
        """
        Helper method to remove all override contexts, this is called automatically
        during the after request phase in Flask. However it is provided here
        if override contexts need to be cleared independent of the application
        context.

        If an override context is found that originated from an OverrideManager
        instance not controlled by the Allows object, a ``RuntimeError``
        will be raised.
        """
        while self.overrides.current is not None:
            self.overrides.pop()


def __get_allows():
    "Internal helper"
    try:
        return current_app.extensions["allows"]
    except (AttributeError, KeyError):
        raise RuntimeError("Flask-Allows not configured against current app")


def _make_callable(func_or_value):
    if not callable(func_or_value):
        return lambda *a, **k: func_or_value
    return func_or_value


def _call_requirement(req, user, request):
    try:
        return req(user)
    except TypeError:
        warnings.warn(
            "Passing request to requirements is now deprecated"
            " and will be removed in 1.0",
            DeprecationWarning,
            stacklevel=2,
        )

        return req(user, request)


allows = LocalProxy(__get_allows, name="flask-allows")
