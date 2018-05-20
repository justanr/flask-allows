import operator
from abc import ABCMeta, abstractmethod
from functools import wraps

from flask import request
from flask._compat import with_metaclass

from .allows import _call_requirement
from .overrides import current_overrides


class Requirement(with_metaclass(ABCMeta)):
    """
    Base for object based Requirements in Flask-Allows. This is quite
    useful for requirements that have complex logic that is too much to fit
    inside of a single function.
    """

    @abstractmethod
    def fulfill(self, user, request=None):
        """
        Abstract method called to verify the requirement against the current
        user and request.

        .. versionchanged:: 0.5.0
            Passing request is now deprecated, pending removal in version 1.0.0

        :param user: The current identity
        :param request: The current request.
        """
        return NotImplemented

    def __call__(self, user, request):
        return _call_requirement(self.fulfill, user, request)

    def __repr__(self):
        return "<{}()>".format(self.__class__.__name__)


class ConditionalRequirement(Requirement):
    """
    Used to combine requirements together in ways other than all-or-nothing,
    such as with an or-reducer (any requirement must be True)::

        from flask_allows import Or

        requires(Or(user_is_admin, user_is_moderator))

    or negating a requirement::

        from flask_allows import Not

        requires(Not(user_logged_in))

    Combinations may also nested::

        Or(user_is_admin, And(user_is_moderator, HasPermission('view_admin')))

    Custom combinators may be built by creating an instance of ConditionalRequirement
    and supplying any combination of its keyword parameters

    This class is also exported under the ``C`` alias.


    :param requirements: Collection of requirements to combine into
        one logical requirement
    :param op: Optional, Keyword only. A binary operator that accepts two
        booleans and returns a boolean.
    :param until: Optional, Keyword only. A boolean to short circuit on (e.g.
        if provided with True, then the first True evaluation to return from a
        requirement ends verification)
    :param negated: Optional, Keyword only. If true, then the
        ConditionalRequirement will return the opposite of what it actually
        evaluated to (e.g. ``ConditionalRequirement(user_logged_in, negated=True)``
        returns False if the user is logged in)
    """

    def __init__(self, *requirements, **kwargs):
        self.requirements = requirements
        self.op = kwargs.get("op", operator.and_)
        self.until = kwargs.get("until")
        self.negated = kwargs.get("negated")

    @classmethod
    def And(cls, *requirements):
        """
        Short cut helper to construct a combinator that uses
        :meth:`operator.and_` to reduce requirement results and stops
        evaluating on the first False.

        This is also exported at the module level as ``And``
        """
        return cls(*requirements, op=operator.and_, until=False)

    @classmethod
    def Or(cls, *requirements):
        """
        Short cut helper to construct a combinator that uses
        :meth:`operator.or_` to reduce requirement results and stops evaluating
        on the first True.

        This is also exported at the module level as ``Or``
        """
        return cls(*requirements, op=operator.or_, until=True)

    @classmethod
    def Not(cls, *requirements):
        """
        Shortcut helper to negate a requirement or requirements.

        This is also exported at the module as ``Not``
        """
        return cls(*requirements, negated=True)

    def fulfill(self, user, request):
        reduced = None

        requirements = self.requirements

        # can't use is because is a proxy
        if current_overrides != None:  # noqa: E711
            requirements = (
                r for r in requirements if r not in current_overrides
            )

        for r in requirements:
            result = _call_requirement(r, user, request)

            if reduced is None:
                reduced = result
            else:
                reduced = self.op(reduced, result)

            if self.until == reduced:
                break

        if reduced is not None:
            return not reduced if self.negated else reduced

        return True

    def __and__(self, require):
        return self.And(self, require)

    def __or__(self, require):
        return self.Or(self, require)

    def __invert__(self):
        return self.Not(self)

    def __repr__(self):
        additional = []

        for name in ["op", "negated", "until"]:
            value = getattr(self, name)
            if not value:
                continue
            additional.append("{0}={1!r}".format(name, value))

        if additional:
            additional = " {}".format(", ".join(additional))
        else:
            additional = ""

        return "<{0} requirements={1!r}{2}>".format(
            self.__class__.__name__, self.requirements, additional
        )

    def __eq__(self, other):
        return (
            isinstance(other, ConditionalRequirement)
            and self.op == other.op
            and self.until == other.until
            and self.negated == other.negated
            and self.requirements == other.requirements
        )

    def __hash__(self):
        return hash((self.requirements, self.op, self.until, self.negated))


(C, And, Or, Not) = (
    ConditionalRequirement,
    ConditionalRequirement.And,
    ConditionalRequirement.Or,
    ConditionalRequirement.Not,
)


def wants_request(f):
    """
    Helper decorator for transitioning to user-only requirements, this aids
    in situations where the request may be marked optional and causes an
    incorrect flow into user-only requirements.

    This decorator causes the requirement to look like a user-only requirement
    but passes the current request context internally to the requirement.

    This decorator is intended only to assist during a transitionary phase
    and will be removed in flask-allows 1.0

    See: :issue:`20,27`
    """

    @wraps(f)
    def wrapper(user):
        return f(user, request)

    return wrapper
