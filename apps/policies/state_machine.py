"""The policy lifecycle as one declarative table (ADR-0003, domain-invariants).

Canonical path: new -> quoted -> accepted -> active ("active" == "bound").
Extensions: quoted -> expired/declined, active -> cancelled. Anything not in
TRANSITIONS is refused, and callers must not write a transition row for a move
this module rejects.
"""

from __future__ import annotations

from apps.policies.exceptions import InvalidStateTransition


class State:
    NEW = "new"
    QUOTED = "quoted"
    ACCEPTED = "accepted"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    DECLINED = "declined"


CHOICES = [
    (State.NEW, "New"),
    (State.QUOTED, "Quoted"),
    (State.ACCEPTED, "Accepted"),
    (State.ACTIVE, "Active"),
    (State.EXPIRED, "Expired"),
    (State.CANCELLED, "Cancelled"),
    (State.DECLINED, "Declined"),
]

# None is the genesis: a brand-new policy enters the machine at ``new``.
TRANSITIONS: dict[str | None, set[str]] = {
    None: {State.NEW},
    State.NEW: {State.QUOTED},
    State.QUOTED: {State.ACCEPTED, State.EXPIRED, State.DECLINED},
    State.ACCEPTED: {State.ACTIVE},
    State.ACTIVE: {State.CANCELLED},
    State.EXPIRED: set(),
    State.CANCELLED: set(),
    State.DECLINED: set(),
}


def can_transition(from_state: str | None, to_state: str) -> bool:
    return to_state in TRANSITIONS.get(from_state, set())


def assert_can_transition(from_state: str | None, to_state: str) -> None:
    if not can_transition(from_state, to_state):
        raise InvalidStateTransition(f"Cannot move a policy from {from_state!r} to {to_state!r}.")
