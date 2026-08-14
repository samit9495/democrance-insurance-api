# 0005. dob is DD-MM-YYYY, accepting ISO on input

- Status: accepted
- Date: 2026-08-15

## Context

The brief's sample payload gives `dob: "25-06-1991"` (REQUIREMENTS 2.2). This is
neither ISO 8601 nor unambiguous against the US `MM-DD-YYYY` convention. Reading
it as US format would silently mis-rate customers, because age drives the premium.

## Decision

Treat `dob` as `DD-MM-YYYY` (D2). On input, accept both `DD-MM-YYYY` and ISO
`YYYY-MM-DD`; on output, always render `DD-MM-YYYY` to match the brief exactly.
Implement this once as a reusable `FlexibleDateField`
(`apps/common/fields.py`), used by every serializer that carries a date.

## Consequences

- The brief's own payload round-trips unchanged, and ISO input is accepted as a
  convenience without ambiguity (DD-MM-YYYY is tried first).
- Impossible dates (`31-02-1991`), the wrong separators (`25/06/1991`) and
  non-dates are rejected with a 400 in the uniform envelope.
- Covered by `apps/common/tests/test_fields.py`; affects REQ-P1-4 and every
  dated response.
