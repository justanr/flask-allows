import warnings
from functools import wraps
from itertools import chain

from flask import current_app, request
from werkzeug.datastructures import ImmutableDict
from werkzeug.exceptions import Forbidden
from werkzeug.local import LocalProxy

from .additional import Additional, AdditionalManager
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

    def __init__(
        self, app=None, identity_loader=None, throws=Forbidden, on_fail=None
    ):
        self._identity_loader = identity_loader
        self.throws = throws

        self.on_fail = _make_callable(on_fail)
        self.overrides = OverrideManager()
        self.additional = AdditionalManager()

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
            self.additional.push(Additional())

        @app.after_request
        def cleanup(response):
            self.clear_all_overrides()
            self.clear_all_additional()
            return response

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

        identity = opts.get("identity")
        on_fail = opts.get("on_fail")
        throws = opts.get("throws")

        def decorator(f):

            @wraps(f)
            def allower(*args, **kwargs):

                result = self.run(
                    requirements,
                    identity=identity,
                    on_fail=on_fail,
                    throws=throws,
                    f_args=args,
                    f_kwargs=kwargs,
                )

                # authorization failed
                if result is not None:
                    return result

                return f(*args, **kwargs)

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

        This method takes into account both additional and overridden
        requirements, with overridden requirements taking precedence::

            allows.additional.push(Additional(Has('foo')))
            allows.overrides.push(Override(Has('foo')))

            allows.fulfill([], user_without_foo)  # return True

        :param requirements: The requirements to check the identity against.
        :param identity: Optional. Identity to use in place of the current
            identity.
        """
        identity = identity or self._identity_loader()

        if self.additional.current:
            all_requirements = chain(
                iter(self.additional.current), requirements
            )
        else:
            all_requirements = iter(requirements)

        if self.overrides.current is not None:
            all_requirements = (
                r for r in all_requirements if r not in self.overrides.current
            )

        return all(
            _call_requirement(r, identity, request) for r in all_requirements
        )

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

    def clear_all_additional(self):
        """
        Helper method to remove all additional contexts, this is called
        automatically during the after request phase in Flask. However it is
        provided here if additional contexts need to be cleared independent of
        the request cycle.

        If an additional context is found that originated from an
        AdditionalManager instance not controlled by the Allows object, a
        ``RuntimeError`` will be raised.
        """
        while self.additional.current is not None:
            self.additional.pop()

    def run(
        self,
        requirements,
        identity=None,
        throws=None,
        on_fail=None,
        f_args=(),
        f_kwargs=ImmutableDict(),
        use_on_fail_return=True,
    ):
        """
        Used to preform a full run of the requirements and the options given,
        this method will invoke on_fail and/or throw the appropriate exception
        type. Can be passed arguments to call on_fail with via f_args (which are
        passed positionally) and f_kwargs (which are passed as keyword).

        :param requirements: The requirements to check
        :param identity: Optional. A specific identity to use for the check
        :param throws: Optional. A specific exception to throw for this check
        :param on_fail: Optional. A callback to invoke after failure,
            alternatively a value to return when failure happens
        :param f_args: Positional arguments to pass to the on_fail callback
        :param f_kwargs: Keyword arguments to pass to the on_fail callback
        :param use_on_fail_return: Boolean (default True) flag to determine
            if the return value should be used. If true, the return value
            will be considered, else failure will always progress to
            exception raising.
        """

        throws = throws or self.throws
        on_fail = _make_callable(
            on_fail
        ) if on_fail is not None else self.on_fail

        if not self.fulfill(requirements, identity):
            result = on_fail(*f_args, **f_kwargs)
            if use_on_fail_return and result is not None:
                return result
            raise throws


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
