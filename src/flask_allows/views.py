from functools import wraps

from flask import current_app, request

from .allows import allows


def _get_executing_handler():
    return current_app.view_functions[request.endpoint]


def requires(*requirements, **opts):
    """
    Standalone decorator to apply requirements to routes, either function
    handlers or class based views::

        @requires(MyRequirement())
        def a_view():
            pass

        class AView(View):
            decorators = [requires(MyRequirement())]

    :param requirements: The requirements to apply to this route
    :param throws: Optional. Exception or exception instance to throw if
        authorization fails.
    :param on_fail: Optional. Value or function to use when authorization
        fails.
    :param identity: Optional. An identity to use in place of the currently
        loaded identity.
    """

    identity = opts.get("identity")
    on_fail = opts.get("on_fail")
    throws = opts.get("throws")

    def decorator(f):

        @wraps(f)
        def allower(*args, **kwargs):

            result = allows.run(
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


def exempt_from_requirements(f):
    """
    Used to exempt a route handler from ambient requirement handling unless it
    is explicitly decorated with a requirement runner::

        @bp.route('/')
        @exempt_from_requirements
        def greeting_area():
            return "Hello!"

    To use with a class based view, apply it to the class level decorators
    attribute::

        class SomeCBV(View):
            decorators = [exempt_from_requirements]

            def get(self):
                return "Hello!"


    .. note::

        You cannot exempt individual methods of a class based view with this
        decorator, e.g. the follow will not work::

            class SomeCBV(MethodView):

                @exempt_from_requirements
                def get(self):
                    return "Hello!"


        Any permissioning applied at the blueprint level would still affect
        this route.


    :param f: The route handler to be decorated.
    """

    f.__allows_exempt__ = True
    return f


def guard_blueprint(requirements, identity=None, throws=None, on_fail=None):
    """
    Used to protect an entire blueprint with a set of requirements. If a route
    handler inside the blueprint should be exempt, then it may be decorated
    with the :func:`~flask_allows.views.exempt_from_requirements` decorator.

    This function should be registered as a before_request handler on the
    blueprint and provided with the requirements to guard the blueprint with::

        my_bp = Blueprint(__name__, 'namespace')
        my_bp.before_request(guard_blueprint(MustBeLoggedIn()))

    `identity`, `on_fail` and `throws` may also be provided but are optional.
    If on_fails returns a non-None result, that will be considered the return
    value of the routing::


        from flask import flash, redirect

        def flash_and_redirect(message, level, endpoint):
            def _(*a, **k):
                flash(message, level)
                return redirect(endpoint)
            return _

        bp = Blueprint(__name__, 'namespace')
        bp.before_request(
            guard_blueprint(
                [MustBeLoggedIn()],
                on_fail=flash_and_redirect(
                    "Please login in first",
                    "warning",
                    "login"
                )
            )
        )

    If needed, this guard may be applied multiple times. This may be useful
    if different conditions should result in different `on_fail` mechanisms
    being invoked::

        bp = Blueprint(__name__, "admin_panel")
        bp.before_request(
            guard_blueprint(
                [MustBeLoggedIn()],
                on_fail=flash_and_redirect(
                    "Please login in first",
                    "warning",
                    "login"
                )
            )
        )
        bp.before_request(
            guard_blueprint(
                [MustBeAdmin()],
                on_fail=flash_and_redirect(
                    "You are not an admin.",
                    "danger",
                    "index"
                )
            )
        )

    :param requirements: An iterable of requirements to apply to every request
        routed to the blueprint.
    :param identity: Optional. The identity that should be used for fulfilling
        requirements on the blueprint level.
    :param throws: Optional. Exception or exception type to be thrown if
        authorization fails.
    :param on_fail: Optional. Value or function to use if authorization fails.
    """

    def guarder():
        is_exempt = getattr(
            _get_executing_handler(), "__allows_exempt__", False
        )

        if not is_exempt:
            return allows.run(
                requirements, identity=identity, on_fail=on_fail, throws=throws
            )
        return None

    return guarder
