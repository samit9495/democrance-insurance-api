"""Phase 4: the policy state machine (domain-invariants — 100% coverage).

Every legal transition is permitted and every illegal one is refused with
InvalidStateTransition. The table is the single source of truth.
"""

import pytest

from apps.policies.exceptions import InvalidStateTransition
from apps.policies.state_machine import State, assert_can_transition, can_transition

LEGAL = [
    (None, State.NEW),
    (State.NEW, State.QUOTED),
    (State.QUOTED, State.ACCEPTED),
    (State.QUOTED, State.EXPIRED),
    (State.QUOTED, State.DECLINED),
    (State.ACCEPTED, State.ACTIVE),
    (State.ACTIVE, State.CANCELLED),
]

ILLEGAL = [
    (None, State.QUOTED),
    (State.NEW, State.ACCEPTED),
    (State.QUOTED, State.ACTIVE),
    (State.ACCEPTED, State.ACCEPTED),
    (State.ACTIVE, State.ACTIVE),
    (State.EXPIRED, State.ACCEPTED),
    (State.CANCELLED, State.ACTIVE),
    (State.ACTIVE, State.QUOTED),
]


@pytest.mark.parametrize(("from_state", "to_state"), LEGAL)
def test_legal_transitions_are_allowed(from_state, to_state):
    assert can_transition(from_state, to_state) is True
    assert_can_transition(from_state, to_state)  # must not raise


@pytest.mark.parametrize(("from_state", "to_state"), ILLEGAL)
def test_illegal_transitions_are_refused(from_state, to_state):
    assert can_transition(from_state, to_state) is False
    with pytest.raises(InvalidStateTransition):
        assert_can_transition(from_state, to_state)
