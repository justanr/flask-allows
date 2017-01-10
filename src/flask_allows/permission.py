from .allows import _allows


class Permission(object):
    """Permission works with the current instance of Allows to provide a context
    for checking requirements. If the requirements are not met, an exception is
    raised:

        ..code-block:: Python

        from flask_allows.permissions import Permission
        from myrequirements import IsAdmin

        def some_function():
            with Permission(IsAdmin()):
                return "Awesome!"

    By default, Permission will delegate to the current Allows instance for
    identity loading, however, an explicit identity can be provided by passing
    an identity keyword.

        ..code-block:: Python

        with Permission(IsAdmin(), identity=user):
            print("Doing the thing...")

    Permission also delegates to the current Allows instance for determining
    what exception to throw. But by providing an exception with the `throws`
    keyword, it can be overriden:

        ..code-block:: Python

        with Permission(IsAdmin(), throws=Forbidden("You ain't no admin!")):
            print("Happy message board adminstrator day!")

    In addition to being a context manager, Permission can be used as a boolean
    as well. In this case, Permission does not raise an exception if the
    requirements are not met.

        ..code-block:: Python

        if Permission(IsAdmin()):
            add_admin_stuff_to_response()
    """
    def __init__(self, *requirements, **opts):
        self.ext = _allows._get_current_object()
        self.requirements = requirements
        self.throws = opts.get('throws', self.ext.throws)
        self.identity = opts.get('identity')

        if isinstance(self.throws, type):
            self.throw_type = self.throws
        else:
            self.throw_type = type(self.throws)

    def __bool__(self):
        return self.ext.fulfill(self.requirements, identity=self.identity)

    __nonzero__ = __bool__

    def __enter__(self):
        if not self:
            raise self.throws

    def __exit__(self, exctype, value, tb):
        pass
