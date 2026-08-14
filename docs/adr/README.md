# Architecture Decision Records

Each ADR records one real ambiguity in the brief or the sequence diagram and the
resolution chosen for it. The short form is deliberate: context, decision,
consequences. See [../REQUIREMENTS.md](../REQUIREMENTS.md) §2.2 for where these
ambiguities are first discussed, and the `write-adr` convention for numbering.

Every ADR that changes the wire contract is backed by at least one named test in
[../MASTER-PLAN.md](../MASTER-PLAN.md).

## Index

| ADR | Decision | Traceability | Written in |
|-----|----------|--------------|------------|
| 0001 | `create_customer` keeps its RPC-style path, with a REST alias `POST /customers/` | ENH-01, D1 | Phase 2 |
| 0002 | One overloaded `POST /quote/` dispatches create / accept / pay by payload keys | ENH-01, D1 | Phase 6 |
| 0003 | Canonical states `new -> quoted -> accepted -> active`; "bound" is a synonym of `active` | REQ-P2-5 | Phase 4 |
| 0004 | `premium` is server-computed and read-only on input (rejected, not ignored) | REQ-P2-2, ADR-0004 | Phase 6 |
| 0005 | `dob` is `DD-MM-YYYY` on output, accepting ISO too, via a reusable `FlexibleDateField` | D2 | Phase 2 |
| 0006 | DB-driven, date-versioned `RatingRule` table instead of hardcoded rates | D6, ENH-03 | Phase 3 |
| 0007 | A custom immutable `PolicyStateTransition` instead of `django-simple-history` | D7, ENH-06 | Phase 4 |
| 0008 | One `User` table with a `role` discriminator, plus the `DEMO_OPEN_API` escape hatch | D3, D4, ENH-09 | Phase 9 |

ADRs 0001–0005 are already specified in prose in REQUIREMENTS.md §2.2; 0006–0008
formalise decisions D6, D7 and D3/D4 that the specification makes but had not yet
been recorded as standalone records. Each file is authored in the phase noted
above, alongside the code and tests that implement the decision.
