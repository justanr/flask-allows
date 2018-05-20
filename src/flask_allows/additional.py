from contextlib import contextmanager
from functools import wraps

from werkzeug.local import LocalProxy, LocalStack

_additional_ctx_stack = LocalStack()


@LocalProxy
def current_additions():
    """
    Proxy to the currently added requirements
    """
    rv = _additional_ctx_stack.top
    if rv is None:
        return None
    return rv[1]


def _isinstance(f):

    @wraps(f)
    def check(self, other):
        if not isinstance(other, Additional):
            return NotImplemented
        return f(self, other)

    return check


class Additional(object):
    """
    Container object that allows to run extra requirements on checks. These
    additional requirements will be run at most once per check and will
    occur in no guarenteed order.

    Requirements can be added by passing them into the constructor or
    by calling the ``add`` method. They can be removed from this object
    by calling the ``remove`` method. To check if a requirement has been added
    to the current conext, you may call ``is_added`` or use ``in``::

        some_req in additional
        additional.is_added(some)req)

    Additional objects can be iterated and length checked::

        additional = Additional(some_req)
        assert len(additional) == 1
        assert list(additional) == [some_req]

    Additional objects may be combined and compared to each other with the following
    operators:

    ``+`` creates a new additional object by combining two others, the new
    additional supplies all requirements that both parents did.

    ``+=`` similar to ``+`` except it is an inplace update.

    ``-`` creates a new additional instance by removing any requirements from
    the first instance that are contained in the second instance.

    ``-=`` similar to ``-`` except it is an inplace update.

    ``==`` compares two additional instances and returns true if both have
    the same added requirements.

    ``!=`` similar to ``!=`` except returns true if both have different
    requirements contained in them.
    """

    def __init__(self, *requirements):
        self._requirements = set(requirements)

    def add(self, requirement, *requirements):
        self._requirements.update((requirement,) + requirements)

    def remove(self, requirement, *requirements):
        self._requirements.difference_update((requirement,) + requirements)

    @_isinstance
    def __add__(self, other):
        requirements = self._requirements | other._requirements
        return Additional(*requirements)

    @_isinstance
    def __iadd__(self, other):
        if len(other._requirements) > 0:
            self._requirements.add(*other._requirements)
        return self

    @_isinstance
    def __sub__(self, other):
        requirements = self._requirements - other._requirements
        return Additional(*requirements)

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

    def __iter__(self):
        return iter(self._requirements)

    def is_added(self, requirement):
        return requirement in self._requirements

    def __contains__(self, requirement):
        return self.is_added(requirement)

    def __len__(self):
        return len(self._requirements)

    def __bool__(self):
        return len(self) != 0

    __nonzero__ = __bool__

    def __repr__(self):
        return "Additional({!r})".format(self._requirements)


class AdditionalManager(object):
    """
    Used to manage the process of adding and removing additional requirements
    to be run. This class shouldn't be used directly, instead use
    ``allows.additional`` to access these controls.
    """

    def push(self, additional, use_parent=False):
        """
        Binds an additional to the current context, optionally use the
        current additionals in conjunction with this additional

        If ``use_parent`` is true, a new additional is created from the
        parent and child additionals rather than manipulating either
        directly.
        """
        current = self.current
        if use_parent and current:
            additional = current + additional

        _additional_ctx_stack.push((self, additional))

    def pop(self):
        """
        Pops the latest additional context.

        If the additional context was pushed by a different additional manager,
        a ``RuntimeError`` is raised.
        """
        rv = _additional_ctx_stack.pop()
        if rv is None or rv[0] is not self:
            raise RuntimeError(
                "popped wrong additional context ({} instead of {})".format(
                    rv, self
                )
            )

    @property
    def current(self):
        """
        Returns the current additional context if set otherwise None
        """
        try:
            return _additional_ctx_stack.top[1]
        except TypeError:
            return None

    @contextmanager
    def additional(self, additional, use_parent=False):
        """
        Allows temporarily pushing an additional context, yields the new context
        into the following block.
        """
        self.push(additional, use_parent)
        yield self.current
        self.pop()
