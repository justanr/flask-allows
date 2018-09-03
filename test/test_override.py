import pytest

from flask_allows.overrides import (
    Override,
    OverrideManager,
    _override_ctx_stack,
    current_overrides,
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
        return (
            isinstance(other, AClassRequirement) and self.the_value == other.the_value
        )


class TestCurrentOverrides(object):
    def test_current_overrides_with_no_context_returns_None(self):
        assert current_overrides == None  # noqa: E711

    def test_current_overrides_returns_active_context(self, never):
        manager = OverrideManager()
        o = Override(never)

        manager.push(o)

        assert o == current_overrides

        manager.pop()

    def test_current_overrides_points_towards_temporary_context(self, never, always):
        manager = OverrideManager()
        manager.push(Override(never))

        o = Override(always)

        with manager.override(o):
            assert o == current_overrides

        manager.pop()


class TestOverride(object):
    def test_shows_if_requirement_is_overridden(self):
        override = Override(some_requirement)
        assert override.is_overridden(some_requirement)
        assert some_requirement in override

    def test_can_add_two_overrides_together(self):
        override_1 = Override(some_requirement)
        override_2 = Override(some_other_requirement)
        added_override = override_1 + override_2
        assert some_requirement in added_override
        assert some_other_requirement in added_override

    def test_can_inplace_add_two_overrides(self):
        override_1 = Override(some_requirement)
        override_1 += Override(some_other_requirement)
        assert some_requirement in override_1
        assert some_other_requirement in override_1

    def test_can_take_the_difference_of_two_overrides(self):
        override_1 = Override(some_requirement, some_other_requirement)
        override_2 = Override(some_other_requirement)
        subbed_override = override_1 - override_2
        assert some_requirement in subbed_override
        assert some_other_requirement not in subbed_override

    def test_can_take_the_difference_of_two_overrides_in_place(self):
        override_1 = Override(some_other_requirement, some_requirement)
        override_1 -= Override(some_other_requirement)
        assert some_requirement in override_1
        assert some_other_requirement not in override_1

    def test_can_add_single_requirement_to_override(self):
        override = Override()
        override.add(some_requirement)
        assert some_requirement in override

    def test_can_remove_a_requirement_from_override(self):
        override = Override(some_requirement)
        override.remove(some_requirement)
        assert some_requirement not in override


class TestOverrideManager(object):
    def test_override_manager_populates_overrides_local(self):
        manager = OverrideManager()
        override = Override(some_requirement)
        manager.push(override)
        assert some_requirement in current_overrides

    def test_manager_throws_if_different_context_popped(self):
        manager = OverrideManager()
        manager.push(Override())
        manager2 = OverrideManager()

        with pytest.raises(RuntimeError) as excinfo:
            manager2.pop()

        assert "popped wrong override context" in str(excinfo.value)

    def test_popping_unpopulated_override_errors(self):
        manager = OverrideManager()

        with pytest.raises(RuntimeError) as excinfo:
            manager.pop()

        assert "popped wrong override context" in str(excinfo.value)

    def test_override_context_manager(self):
        manager = OverrideManager()
        o = Override()

        with manager.override(o):
            assert _override_ctx_stack.top[1] is o

        assert _override_ctx_stack.top is None

    def test_override_with_use_parent_combines_both(self):
        manager = OverrideManager()

        def parent_requirement(user):
            return True

        def child_requirement(user):
            return True

        parent = Override(parent_requirement)
        child = Override(child_requirement)

        expected = Override(parent_requirement, child_requirement)

        with manager.override(parent):
            with manager.override(child, use_parent=True):
                assert expected == manager.current
