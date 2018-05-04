from functools import wraps

from .allows import allows


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
