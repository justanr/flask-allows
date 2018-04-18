from contextlib import contextmanager

from werkzeug.local import LocalProxy, LocalStack

_override_ctx_stack = LocalStack()


@LocalProxy
def overrides():
    rv = _override_ctx_stack.top
    if rv is None:
        raise RuntimeError("No override manager context active")
    return rv[1]


class Override(object):
    """
    Container object to manage which requirements should and should not
    be overridden. On its own, it's fairly useless but when used with
    OverrideManager it's able to be used by the rest of the application
    """

    def __init__(self, *requirements):
        self._requirements = set(requirements)

    def add(self, requirement, *requirements):
        self._requirements.update((requirement, ) + requirements)

    def remove(self, requirement, *requirements):
        self._requirements.difference_update((requirement, ) + requirements)

    def is_overridden(self, requirement):
        return requirement in self._requirements

    def __contains__(self, other):
        return self.is_overridden(other)

    def __add__(self, other):
        if not isinstance(other, Override):
            return NotImplemented
        requirements = self._requirements | other._requirements
        return Override(*requirements)

    def __iadd__(self, other):
        if not isinstance(other, Override):
            return NotImplemented
        if len(other._requirements) > 0:
            self.add(*other._requirements)
        return self

    def __sub__(self, other):
        if not isinstance(other, Override):
            return NotImplemented
        requirements = self._requirements - other._requirements
        return Override(*requirements)

    def __isub__(self, other):
        if not isinstance(other, Override):
            return NotImplemented
        if len(other._requirements) > 0:
            self.remove(*other._requirements)
        return self


class OverrideManager(object):
    """
    Used to manage the process of overriding and removing overrides.
    This class shouldn't be used directly, instead use allows.overrides
    to create this object.
    """

    def push(self, override, use_parent=False):
        """
        Binds an override to the current context, optionally use the
        current overrides in conjunction with this override
        """
        current = self.current
        if use_parent and current:
            override += current

        _override_ctx_stack.push((self, override))

    def pop(self):
        """
        Pops the latest override context
        """
        rv = _override_ctx_stack.pop()
        if rv is None or rv[0] is not self:
            raise RuntimeError(
                'popped wrong override context ({} instead of {})'.
                format(rv, self)
            )

    @property
    def current(self):
        try:
            return _override_ctx_stack.top[1]
        except TypeError:
            return None

    @contextmanager
    def override(self, requirement, *requirements, use_parent=False):
        self.push(Override(requirement, *requirements), use_parent)
        yield self
        self.pop()
