from contextlib import contextmanager
from functools import wraps

from werkzeug.local import LocalProxy, LocalStack

_override_ctx_stack = LocalStack()


@LocalProxy
def current_overrides():
    """
    Proxy to the currently pushed override context.
    """
    rv = _override_ctx_stack.top
    if rv is None:
        return None
    return rv[1]


def _isinstance(f):

    @wraps(f)
    def check(self, other):
        if not isinstance(other, Override):
            return NotImplemented
        return f(self, other)

    return check


class Override(object):
    """
    Container object that allows selectively disabling requirements.

    Requirements can be disabled by passing them to the constructor or
    by calling the ``add`` method. They can be re-enabled by calling the
    ``remove`` method. To check if a requirement is currently disabled, you
    may call either ``is_overridden`` or use ``in``.

    Override objects can be combined and compared to each other with the following
    operators:

    ``+`` creates a new overide object by combining two others, the new
    override overrides all requirements that both parents did.

    ``+=`` similar to ``+`` except it is an inplace update.

    ``-`` creates a new override instance by removing any overrides from
    the first instance that are contained in the second instance.

    ``-=`` similar to ``-`` except it is an inplace update

    ``==`` compares two overrides and returns true if both have the same
    disabled requirements.

    ``!=`` similar to ``==`` except returns true if both have different
    disabled requirements.
    """

    def __init__(self, *requirements):
        self._requirements = set(requirements)

    def add(self, requirement, *requirements):
        """
        Adds one or more requirements to the override context.
        """
        self._requirements.update((requirement,) + requirements)

    def remove(self, requirement, *requirements):
        """
        Removes one or more requirements from the override context.
        """
        self._requirements.difference_update((requirement,) + requirements)

    def is_overridden(self, requirement):
        """
        Checks if a particular requirement is current overridden. Can also
        be used as ``in``::

            override = Override()
            override.add(is_admin)
            override.is_overridden(is_admin)  # True
            is_admin in override  # True

        """
        return requirement in self._requirements

    def __contains__(self, other):
        return self.is_overridden(other)

    @_isinstance
    def __add__(self, other):
        requirements = self._requirements | other._requirements
        return Override(*requirements)

    @_isinstance
    def __iadd__(self, other):
        if len(other._requirements) > 0:
            self.add(*other._requirements)
        return self

    @_isinstance
    def __sub__(self, other):
        requirements = self._requirements - other._requirements
        return Override(*requirements)

    @_isinstance
    def __isub__(self, other):
        if len(other._requirements) > 0:
            self.remove(*other._requirements)
        return self

    @_isinstance
    def __eq__(self, other):
        return self._requirements == other._requirements

    @_isinstance
    def __ne__(self, other):
        return not self == other

    def __len__(self):
        return len(self._requirements)

    def __bool__(self):
        return len(self) != 0

    __nonzero__ = __bool__

    def __repr__(self):
        return "Override({!r})".format(self._requirements)


class OverrideManager(object):
    """
    Used to manage the process of overriding and removing overrides.
    This class shouldn't be used directly, instead use ``allows.overrides``
    to access these controls.
    """

    def push(self, override, use_parent=False):
        """
        Binds an override to the current context, optionally use the
        current overrides in conjunction with this override

        If ``use_parent`` is true, a new override is created from the
        parent and child overrides rather than manipulating either
        directly.
        """
        current = self.current
        if use_parent and current:
            override = current + override

        _override_ctx_stack.push((self, override))

    def pop(self):
        """
        Pops the latest override context.

        If the override context was pushed by a different override manager,
        a ``RuntimeError`` is raised.
        """
        rv = _override_ctx_stack.pop()
        if rv is None or rv[0] is not self:
            raise RuntimeError(
                "popped wrong override context ({} instead of {})".format(
                    rv, self
                )
            )

    @property
    def current(self):
        """
        Returns the current override context if set otherwise None
        """
        try:
            return _override_ctx_stack.top[1]
        except TypeError:
            return None

    @contextmanager
    def override(self, override, use_parent=False):
        """
        Allows temporarily pushing an override context, yields the new context
        into the following block.
        """
        self.push(override, use_parent)
        yield self.current
        self.pop()
