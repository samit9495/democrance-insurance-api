# 0008. One User table with a role, plus a DEMO_OPEN_API escape hatch

- Status: accepted
- Date: 2026-08-15

## Context

The brief asks whether "users" and "customers" are the same thing (D3), and it
must be trivially demoable without a login dance while still proving a
locked-down posture (D4). Most insured customers never log in — they are created
by an agent from a bare JSON payload with no password.

## Decision

Keep a single custom `User` credential store with a `role` discriminator
(`staff`/`agent`/`customer`) and a separate `Customer` business record linked by
a nullable `OneToOne`. Authorise with deny-by-default DRF permissions:
`DemoOrAuthenticated` globally and `DemoOrStaff` on customer creation. A customer
principal is scoped in `get_queryset`, so it gets **404 not 403** for records it
may not see. `DEMO_OPEN_API` (default true for the demo) admits anonymous callers
to the diagram endpoints; it is logged loudly at startup and the permission
matrix is tested in **both** modes so the secure configuration is proven.

## Consequences

- One auth pipeline, one password policy, one token issuer (simplejwt with
  rotation + blacklist); logout genuinely revokes.
- `/me/` stays `IsAuthenticated` even in demo mode — it is about the caller.
- Turning `DEMO_OPEN_API` off flips every diagram endpoint to 401-for-anonymous
  with no code change. Affects REQ-P4-2, D3, D4, ENH-09.
