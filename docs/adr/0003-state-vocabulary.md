# 0003. Canonical state vocabulary and a declarative machine

- Status: accepted
- Date: 2026-08-15

## Context

The sequence diagram drives a policy through `quote` → `accepted` → `active`
(REQUIREMENTS 2.1), and the brief also talks about a policy being "bound". These
are the same idea under two names, and the brief does not enumerate the illegal
moves. Left implicit, a policy could be accepted twice or activated straight from
`new`.

## Decision

Adopt the canonical lifecycle `new -> quoted -> accepted -> active`, where
`active` is the bound state ("bound" is a documented synonym, not a separate
state). Model the whole machine as one declarative table in
`apps/policies/state_machine.py`; anything not in the table raises
`InvalidStateTransition` (HTTP 409) and no audit row is written. Extensions
`quoted -> expired/declined` and `active -> cancelled` are included (ENH-04).

## Consequences

- The diagram's `status: "accepted"` and `status: "active"` map directly onto
  transitions, and quoting logs two moves (`-> new`, `new -> quoted`) so the
  history reads as a full narrative.
- Illegal moves (`quoted -> active`, `active -> active`, accepting an expired
  quote) are refused uniformly and are individually tested; the machine is at
  100% coverage. Affects REQ-P2-5.
