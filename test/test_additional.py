import pytest

from flask_allows.additional import (
    Additional,
    AdditionalManager,
    _additional_ctx_stack,
    current_additions,
)
from flask_allows.requirements import Requirement


def some_requirement(user):
    return True


def some_other_requirement(user):
    return False


class AClassRequirement(Requirement):

    def __init__(self, the_value):
        self.the_value = the_value

    def fulfill(self, user):
        return True

    def __hash__(self):
        return hash(self.the_value)

    def __eq__(self, other):
        return isinstance(
            other, AClassRequirement
        ) and self.the_value == other.the_value


class TestCurrentAdditional(object):

    def test_current_additions_with_no_context_returns_None(self):
        assert current_additions == None  # noqa: E711

    def test_current_additions_returns_active_context(self, never):
        manager = AdditionalManager()
        o = Additional(never)

        manager.push(o)

        assert o == current_additions

        manager.pop()

    def test_current_additions_points_towards_temporary_context(
        self, never, always
    ):
        manager = AdditionalManager()
        manager.push(Additional(never))

        o = Additional(always)

        with manager.additional(o):
            assert o == current_additions

        manager.pop()


class TestAdditional(object):

    def test_shows_if_requirement_is_added(self):
        additional = Additional(some_requirement)
        assert additional.is_added(some_requirement)
        assert some_requirement in additional

    def test_can_add_two_additionals_together(self):
        additional_1 = Additional(some_requirement)
        additional_2 = Additional(some_other_requirement)
        added_additional = additional_1 + additional_2
        assert some_requirement in added_additional
        assert some_other_requirement in added_additional

    def test_can_inplace_add_two_additionals(self):
        additional_1 = Additional(some_requirement)
        additional_1 += Additional(some_other_requirement)
        assert some_requirement in additional_1
        assert some_other_requirement in additional_1

    def test_can_take_the_difference_of_two_additionals(self):
        additional_1 = Additional(some_requirement, some_other_requirement)
        additional_2 = Additional(some_other_requirement)
        subbed_additional = additional_1 - additional_2
        assert some_requirement in subbed_additional
        assert some_other_requirement not in subbed_additional

    def test_can_take_the_difference_of_two_additionals_in_place(self):
        additional_1 = Additional(some_other_requirement, some_requirement)
        additional_1 -= Additional(some_other_requirement)
        assert some_requirement in additional_1
        assert some_other_requirement not in additional_1

    def test_can_add_single_requirement_to_additional(self):
        additional = Additional()
        additional.add(some_requirement)
        assert some_requirement in additional

    def test_can_remove_a_requirement_from_additional(self):
        additional = Additional(some_requirement)
        additional.remove(some_requirement)
        assert some_requirement not in additional


class TestAdditionalManager(object):

    def test_additional_manager_populates_additionals_local(self):
        manager = AdditionalManager()
        additional = Additional(some_requirement)
        manager.push(additional)
        assert some_requirement in current_additions

    def test_manager_throws_if_different_context_popped(self):
        manager = AdditionalManager()
        manager.push(Additional())
        manager2 = AdditionalManager()

        with pytest.raises(RuntimeError) as excinfo:
            manager2.pop()

        assert "popped wrong additional context" in str(excinfo.value)

    def test_popping_unpopulated_additional_errors(self):
        manager = AdditionalManager()

        with pytest.raises(RuntimeError) as excinfo:
            manager.pop()

        assert "popped wrong additional context" in str(excinfo.value)

    def test_additional_context_manager(self):
        manager = AdditionalManager()
        o = Additional()

        with manager.additional(o):
            assert _additional_ctx_stack.top[1] is o

        assert _additional_ctx_stack.top is None

    def test_additional_with_use_parent_combines_both(self):
        manager = AdditionalManager()

        def parent_requirement(user):
            return True

        def child_requirement(user):
            return True

        parent = Additional(parent_requirement)
        child = Additional(child_requirement)

        expected = Additional(parent_requirement, child_requirement)

        with manager.additional(parent):
            with manager.additional(child, use_parent=True):
                assert expected == manager.current
