from functools import wraps

from flask.views import MethodView, View

from .allows import allows, _make_callable


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

    def raiser():
        raise opts.get('throws', allows.throws)

    def fail(*args, **kwargs):
        f = _make_callable(opts.get('on_fail', allows.on_fail))
        res = f(*args, **kwargs)

        if res is not None:
            return res

        raiser()

    def decorator(f):

        @wraps(f)
        def allower(*args, **kwargs):
            if allows.fulfill(requirements, identity=opts.get('identity')):
                return f(*args, **kwargs)
            return fail(*args, **kwargs)

        return allower

    return decorator
