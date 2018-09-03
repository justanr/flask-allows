import operator

import pytest

from flask_allows.allows import Allows
from flask_allows.overrides import Override, OverrideManager
from flask_allows.requirements import (
    And,
    C,
    ConditionalRequirement,
    Not,
    Or,
    Requirement,
    wants_request,
)


def test_cant_create_Requirement():
    with pytest.raises(TypeError) as excinfo:
        Requirement()

    assert "with abstract methods fulfill" in str(excinfo.value)


def test_call_fulfills_with_call(spy):
    spy(object(), object())
    assert spy.called


def test_ConditionalRequirement_defaults(always):
    Cond = ConditionalRequirement(always)

    assert (Cond.requirements, Cond.op, Cond.until, Cond.negated) == (
        (always,),
        operator.and_,
        None,
        None,
    )


def test_empty_Conditional_is_True(member, request):
    Cond = ConditionalRequirement()
    assert Cond(member, request)


def test_custom_ConditionalRequirement(always):
    Cond = ConditionalRequirement(
        always, always, op=operator.xor, negated=True, until=False
    )
    assert (Cond.requirements, Cond.op, Cond.until, Cond.negated) == (
        (always, always),
        operator.xor,
        False,
        True,
    )


def test_AndConditional_defaults(always):
    Cond = And(always)

    assert (Cond.requirements, Cond.op, Cond.until, Cond.negated) == (
        (always,),
        operator.and_,
        False,
        None,
    )


def test_OrConditional_defaults(always):
    Cond = Or(always)

    assert (Cond.requirements, Cond.op, Cond.until, Cond.negated) == (
        (always,),
        operator.or_,
        True,
        None,
    )


def test_NotConditional_defaults(always):
    Cond = Not(always)

    assert (Cond.requirements, Cond.op, Cond.until, Cond.negated) == (
        (always,),
        operator.and_,
        None,
        True,
    )


def test_OrConditional_shortcircuit(always, never, member, request):
    cond = Or(always, never)
    cond.fulfill(member, request)

    assert not never.called


def test_OrConditional_fulfills(always, never, member, request):
    assert Or(always, never)(member, request)
    assert Or(never, always)(member, request)


def test_OrConditional_shortcut(always):
    A = C(always)
    Cond = A | A
    assert (Cond.requirements, Cond.op, Cond.until, Cond.negated) == (
        (A, A),
        operator.or_,
        True,
        None,
    )


def test_AndConditional_shortcircuit(always, never, member, request):
    cond = And(never, always)
    cond.fulfill(member, request)

    assert not always.called


def test_AndConditional_fulfills(always, never, member, request):
    assert not And(always, never)(member, request)
    assert not And(never, always)(member, request)


def test_AndConditional_shortcut(always):
    A = C(always)
    Cond = A & A
    assert (Cond.requirements, Cond.op, Cond.until, Cond.negated) == (
        (A, A),
        operator.and_,
        False,
        None,
    )


def test_NotConditional_shortcut(always):
    A = C(always)
    Cond = ~A

    assert (Cond.requirements, Cond.op, Cond.until, Cond.negated) == (
        (A,),
        operator.and_,
        None,
        True,
    )


def test_NotConditional_singular_true(always, member, request):
    assert not Not(always)(member, request)


def test_NotConditional_singular_false(never, member, request):
    assert Not(never)(member, request)


def test_NotConditional_many_all_true(always, member, request):
    assert not Not(always, always)(member, request)


def test_NotConditional_many_all_false(never, member, request):
    assert Not(never, never)(member, request)


def test_NotConditional_many_mixed(always, never, member, request):
    assert Not(always, never)(member, request)


def test_supports_new_style_requirements(member, request):
    class SomeRequirement(Requirement):
        def fulfill(self, user):
            return True

    assert SomeRequirement()(member, request)


def test_ConditionalRequirement_supports_new_style_requirements(member, request):
    def is_true(user):
        return True

    assert C(is_true)(member, request)


@pytest.mark.regression
def test_wants_request_stops_incorrect_useronly_flow(member, request):
    """
    When a request parameter has a default value, requirement runners will
    incorrectly decide it is a user only requirement and not provide the
    request object to it.
    """
    SENTINEL = object()

    def my_requirement(user, request=SENTINEL):
        return request is not SENTINEL

    allows = Allows(app=None, identity_loader=lambda: member)

    # incorrect flow happens here, only member is passed
    assert not allows.fulfill([my_requirement], member)
    assert allows.fulfill([wants_request(my_requirement)], member)


def test_conditional_skips_overridden_requirements(member, never, always, request):
    manager = OverrideManager()
    manager.push(Override(never))

    reqs = And(never, always)

    assert reqs.fulfill(member, request)

    manager.pop()


def test_conditional_skips_overridden_requirements_even_if_nested(
    member, always, never, request
):
    manager = OverrideManager()
    manager.push(Override(never))

    reqs = And(And(And(always), Or(never)))

    assert reqs.fulfill(member, request)

    manager.pop()
