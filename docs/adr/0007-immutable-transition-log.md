# 0007. A custom immutable transition log, not django-simple-history

- Status: accepted
- Date: 2026-08-15

## Context

The brief asks to expose a policy's state history (REQUIREMENTS 2.1, step 7). A
general library like `django-simple-history` records row-level diffs of every
field on every model — more than is needed, and it answers "what changed" rather
than the question the brief poses: "who moved this policy, when, why, and with
what payment?" (D7).

## Decision

Model history explicitly as an append-only `PolicyStateTransition`
(`from_state`, `to_state`, `actor`, `source` = api|admin|system, `reason`,
`metadata`). Rows are immutable — `save()` raises once a PK exists and the admin
disables add/delete — and services write exactly one row per state change inside
the same transaction as the change itself.

## Consequences

- The history endpoint returns a clean, intentful narrative; `metadata` carries
  the premium and (from Phase 5) the payment reference.
- State and history can never diverge, because both are written in one atomic
  unit; a rejected transition leaves no row.
- No extra dependency, and the audit trail cannot be silently rewritten. Affects
  REQ-P2-5, REQ-P3-4.
