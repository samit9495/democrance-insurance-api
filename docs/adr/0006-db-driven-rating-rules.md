# 0006. DB-driven, date-versioned rating rules

- Status: accepted
- Date: 2026-08-15

## Context

The brief derives a premium from age band and cover but does not say where the
rates live. Hardcoding them in Python (D6) would make every rate change a code
change and a deploy, and would leave historic quotes unexplainable once a rate
moved. Insurers file and version their rates.

## Decision

Model rates as a `RatingRule` table (product, inclusive age band,
`rate_per_1000_cover`, `loading_factor`, `min_premium`, `valid_from`/`valid_to`,
`is_active`), seeded by a data migration and editable in the Django admin
(ENH-03). The engine `calculate_premium(product, age, cover, as_of)` is a pure
function of the table plus the inputs. A DB `CheckConstraint` enforces
`age_band_min <= age_band_max`; `clean()` forbids overlapping active bands within
an intersecting validity window.

## Consequences

- Rates change without a deploy, and a historic quote can be re-explained from
  the rule that was effective on its `as_of` date.
- The seed reproduces the brief's `premium 200.00` exactly, so a fresh clone can
  quote immediately.
- Overlap and inverted bands are impossible to persist (constraint + `clean()`),
  and each is covered by a test. Affects REQ-P2-3.
- The engine has no I/O beyond reading rules, so it is unit-tested to 100%.
