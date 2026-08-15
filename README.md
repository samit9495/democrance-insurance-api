# Democrance Insurance API

A quote-and-policy lifecycle API built for the Democrance technical test:
Django 5.2 LTS + DRF, test-driven, with a DB-driven rating engine, an immutable
audit trail, JWT auth, OpenAPI docs and a no-tooling demo client.

- **What & why:** [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)
- **API contract:** [docs/API.md](docs/API.md) (with a Mermaid sequence diagram)
- **Auth:** [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)
- **Decisions:** [docs/adr/](docs/adr/) (ADRs 0001–0008)
- **Requirement → test map:** [docs/TRACEABILITY.md](docs/TRACEABILITY.md)

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

## Acceptance (copy-paste)

With the server running and `DEMO_OPEN_API=true` (the default), the brief's
headline command works with no auth:

```bash
# 1. create a customer -> 201 with an id
curl -sX POST http://127.0.0.1:8000/api/v1/create_customer/ \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Ben","last_name":"Stokes","dob":"25-06-1991"}'

# 2. quote (premium is computed server-side at 200.00)
curl -sX POST http://127.0.0.1:8000/api/v1/quote/ \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":1,"type":"personal-accident"}'

# 3. accept, then 4. pay/bind
curl -sX POST http://127.0.0.1:8000/api/v1/quote/ -H 'Content-Type: application/json' -d '{"quote_id":1,"status":"accepted"}'
curl -sX POST http://127.0.0.1:8000/api/v1/quote/ -H 'Content-Type: application/json' -d '{"quote_id":1,"status":"active"}'

# 5-7. list, detail, history
curl -s 'http://127.0.0.1:8000/api/v1/policies/?customer_id=1'
curl -s  http://127.0.0.1:8000/api/v1/policies/1/
curl -s  http://127.0.0.1:8000/api/v1/policies/1/history/
```

The same flow is asserted end to end by
`tests/e2e/test_sequence_diagram_flow.py::test_full_diagram_flow`.

> Ids above assume a fresh database (just `make migrate`), so Ben is customer 1.
> If you also ran `make seed`, the demo customer takes id 1 and Ben becomes id 2 —
> adjust `customer_id`/`quote_id` accordingly.

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

```bash
make up      # build + start API and Postgres; migrates and seeds on first boot
make demo    # migrate, seed, and replay the seven-step flow end to end
make down    # stop the stack
```

The image is multi-stage and runs as a non-root user (gunicorn + WhiteNoise);
the container has a `/healthz/` healthcheck and the API waits for a healthy
database before serving. Verified from a cold `docker compose up --build`.

## Deviations from the brief, and scope

The brief invites going beyond the literal ask; where this solution does, it is
recorded as an ADR and an `ENH-` id in [REQUIREMENTS.md §11](docs/REQUIREMENTS.md).
The notable choices:

- **One overloaded `POST /quote/`** (create/accept/pay by payload) to mirror the
  diagram exactly, **plus** REST aliases for clients that prefer them (ADR-0002).
- **Slashless routing.** The diagram writes some paths without a trailing slash;
  every RPC route answers both spellings because `APPEND_SLASH` cannot redirect a
  `POST` without dropping its body (ADR-0001).
- **DB-driven, date-versioned rating** instead of hardcoded rates (ADR-0006), and
  **server-computed premium** rejected on input (ADR-0004).
- **`DEMO_OPEN_API`** opens the seven endpoints for a bare-`curl` review; it is
  off in production and the permission matrix proves the locked-down mode (ADR-0008).

**Deliberately out of scope** (argued in REQUIREMENTS.md §11): dedupe/GDPR
erasure, renewals/endorsements/claims, Celery async, SSO/MFA, multi-currency FX,
and a real payment gateway (the simulator is swappable behind one seam).
