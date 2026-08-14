# Democrance Insurance API

A quote-and-policy lifecycle API built for the Democrance technical test:
Django 5.2 LTS + DRF, test-driven, with a DB-driven rating engine, an immutable
audit trail, JWT auth, OpenAPI docs and a no-tooling demo client.

- **What & why:** [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)
- **API contract:** [docs/API.md](docs/API.md) (with a Mermaid sequence diagram)
- **Auth:** [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)
- **Decisions:** [docs/adr/](docs/adr/) (ADRs 0001–0008)

## Quickstart (local, zero services)

No database to install — it falls back to SQLite when `DATABASE_URL` is unset.

```bash
make install                      # create .venv, install deps
make migrate
make seed                         # demo users + a linked customer
make run                          # http://127.0.0.1:8000/
```

Then open:

- `/` — the single-file demo client that walks all seven diagram steps
- `/api/v1/docs/` — Swagger UI · `/api/v1/redoc/` — ReDoc
- `/admin/` — Django admin (create a superuser with `make superuser`)

> The repo lives in iCloud Drive locally, which is a poor home for a virtualenv.
> Keep the env outside it and point the Makefile at it:
> `make install VENV=$HOME/.venvs/democrance-insurance-api` (then pass the same
> `VENV=…` to other targets).

Demo logins after `make seed` (password `demo-pass-123`): `staff@demo.local`,
`agent@demo.local`, `customer@demo.local`.

## The seven-step flow (the brief)

`create_customer` → `quote` (create) → `quote` (accept) → `quote` (pay/bind) →
`policies` list → policy detail → policy history. For Ben Stokes
(`dob 25-06-1991`, age 35) on `personal-accident` with cover `200000`, the
premium is **`200.00`**. See [docs/API.md](docs/API.md) for payloads.

## Testing & quality

```bash
make test        # full suite + coverage gate (fail-under 90)
make lint        # ruff
make format      # ruff format + --fix
```

The rating engine, the policy state machine and the payment service are held at
**100%** coverage — the parts where a bug costs money. Tests live beside the
code they cover; only cross-app end-to-end tests live in `tests/`.

## Architecture at a glance

- **Thin views, fat services.** Only `apps/policies/services.py` mutates
  `Policy.state`, always writing a `PolicyStateTransition` in the same
  transaction (row-locked), so state and history can never drift.
- **DB-driven rating.** `RatingRule` is date-versioned and admin-editable
  (ADR-0006); `premium` is server-computed and rejected on input (ADR-0004).
- **One overloaded `/quote/`.** Dispatches create/accept/pay by payload keys,
  with clean REST aliases (ADR-0002); every RPC route also answers slashless.
- **Deny by default.** JWT with rotation + blacklist; customer principals are
  scoped so foreign records return 404, not 403. `DEMO_OPEN_API` opens the demo
  and is proven off by the permission matrix (ADR-0008).
- **Uniform errors.** One `{"error": {code, message, details}}` envelope with a
  fixed code→status map.

## Layout

```
apps/
  accounts/   custom User, JWT auth, permissions, seed_demo
  common/     TimeStampedModel, FlexibleDateField, error envelope, pagination
  customers/  Customer model, create + search
  products/   ProductType, RatingRule, rating engine, seed migration
  policies/   Policy, PolicyStateTransition, state machine, services, endpoints
  payments/   Payment + simulate_payment (card/invoice, idempotency)
  search/     unified /search/
  web/        the single-file demo client
config/       split settings (base/dev/test/prod), urls
docs/         requirements, API, auth, ADRs, sequence diagram
```

## Docker

`make up` builds and runs the API against Postgres via Docker Compose; `make
demo` replays the full flow end to end (delivered in Phase 11).
