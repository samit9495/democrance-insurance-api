# 0004. Premium is server-computed and read-only on input

- Status: accepted
- Date: 2026-08-15

## Context

The brief lists `premium` among the fields of the policy/quote object
(REQUIREMENTS 2.2). Read naively, that invites a client to send its own
`premium` — which would make the rating engine meaningless and is an obvious
integrity hole.

## Decision

`premium` is a first-class field that appears in every response, but it is
**never accepted on input**. The quote-create serializer declares only
`customer_id`, `type` and optional `cover`; because it rejects unknown keys
(`StrictFieldsMixin`), a client-supplied `premium` is turned away with a 400
`validation_error` naming the field — rejected, not silently ignored. The value
is always produced by `rating.calculate_premium` from the customer's age band
and the cover.

## Consequences

- The only source of truth for price is the DB-driven rating engine (ADR-0006);
  the wire cannot override it.
- A test posts `premium` to `/quote/` and asserts the 400 envelope carries
  `premium` in its details. Affects REQ-P2-2, REQ-P2-3.
