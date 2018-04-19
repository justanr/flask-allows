import pytest
from flask_allows.overrides import (Override, OverrideManager,
                                    _override_ctx_stack, overrides)
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
        assert some_requirement in overrides

    def test_manager_throws_if_different_context_popped(self):
        assert _override_ctx_stack.top is None
        manager = OverrideManager()
        manager.push(Override())
        manager2 = OverrideManager()

        with pytest.raises(RuntimeError) as excinfo:
            manager2.pop()

        assert 'popped wrong override context' in str(excinfo.value)

    @pytest.mark.fixture(autouse=True)
    def pop_til_you_stop(self):
        while _override_ctx_stack.top is not None:
            _override_ctx_stack.pop()
