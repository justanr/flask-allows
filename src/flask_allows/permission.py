from .allows import allows


class Permission(object):
    """
    Used to check requirements as a boolean or context manager. When used as a
    boolean, it only runs the requirements and returns the raw boolean result::

        p = Permission(is_admin)

        if p:
            print("Welcome to the club!")


    When used as a context manager, it runs both the check and the failure
    handlers if the requirements are not met::

        p = Permission(is_admin)

        with p:
            # will run on_fail and throw before reaching if the
            # requirements on p return False
            print("Welcome to the club!")


    .. note::

        Both the context manager and boolean usages require an active
        application context to use.

    :param requirements: The requirements to check against
    :param throws: Optional, keyword only. Exception to throw when used as a context manager,
        if provided it takes precedence over the exception stored on the current
        application's registered :class:`~flask_allows.allows.Allows` instance
    :param on_fail: Optional, keyword only. Value or function to use as the on_fail when used
        as a context manager, if provided takes precedence over the on_fail
        configured on current application's registered
        :class:`~flask_allows.allows.Allows` instance
    :param identity: Optional, keyword only. An identity to verify against
        instead of the using the loader configured on the current application's
        registered :class:`~flask_allows.allows.Allows` instance

    """

    def __init__(self, *requirements, **opts):
        self.requirements = requirements
        self.throws = opts.get("throws")
        self.identity = opts.get("identity")
        self.on_fail = opts.get("on_fail")

    def __bool__(self):
        return allows.fulfill(self.requirements, identity=self.identity)

    __nonzero__ = __bool__

    def __enter__(self):
        allows.run(
            self.requirements,
            identity=self.identity,
            throws=self.throws,
            on_fail=self.on_fail,
            use_on_fail_return=False,
        )

    def __exit__(self, exctype, value, tb):
        pass
