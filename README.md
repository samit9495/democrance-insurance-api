# Democrance Insurance API

A quote-and-policy lifecycle API built for the Democrance technical test:
Django 5.2 LTS + DRF, test-driven, with a DB-driven rating engine, an immutable
audit trail, JWT auth, OpenAPI docs and a no-tooling demo client.

- **What & why:** [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)
- **API contract:** [docs/API.md](docs/API.md) (with a Mermaid sequence diagram)
- **Auth:** [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)
- **Decisions:** [docs/adr/](docs/adr/) (ADRs 0001–0008)
- **Requirement → test map:** [docs/TRACEABILITY.md](docs/TRACEABILITY.md)

## Running the API — two ways

Pick whichever suits you. Both serve at `http://127.0.0.1:8000/` and behave the
same at the API level.

- **Option A — Local:** fastest, zero services (SQLite fallback). Best for
  reading code, running tests, and a quick edit-reload loop.
- **Option B — Docker:** production-like, runs against PostgreSQL with one
  command. Best for a realistic, reproducible environment.

### Option A — Local (no Docker)

Prerequisites: Python 3.12 and `make`.

```bash
make install                      # create .venv, install deps
make migrate                      # SQLite (no DATABASE_URL needed)
make seed                         # demo users + a linked customer
make run                          # http://127.0.0.1:8000/
```

`.env` is optional — dev settings plus the SQLite fallback work out of the box.
Copy [.env.example](.env.example) to `.env` only if you want to override
defaults (e.g. point `DATABASE_URL` at a local Postgres).

Authentication in this mode: `DEMO_OPEN_API` defaults to `true` (dev settings),
so the seven diagram endpoints work with a bare `curl`. Run `make seed` to get
the demo logins, and `make superuser` to create a Django admin account. See
[Authentication (both modes)](#authentication-both-modes) below.

### Option B — Docker Compose (Postgres)

Prerequisites: Docker Desktop running.

```bash
make up      # build + start API and Postgres; migrates and seeds on first boot
make demo    # migrate, seed, and replay the seven-step flow end to end
make down    # stop the stack
```

This runs the production settings against PostgreSQL. The image is multi-stage
and runs as a non-root user (gunicorn + WhiteNoise); the container has a
`/healthz/` healthcheck and the API waits for a healthy database before serving.
Verified from a cold `docker compose up --build`.

Authentication in this mode: the compose file sets `DEMO_OPEN_API=true` and
`SEED_DEMO=1`, so the demo logins are created automatically on first boot and
the diagram endpoints are open. Create an admin account with
`docker compose exec api python manage.py createsuperuser`. To lock the API
down, set `DEMO_OPEN_API=false` (see below).

### Local vs Docker at a glance

| | Local (Option A) | Docker (Option B) |
|---|---|---|
| Settings | `config.settings.dev` | `config.settings.prod` |
| Database | SQLite fallback (or `DATABASE_URL`) | PostgreSQL (compose service) |
| `DEMO_OPEN_API` from | `.env` / defaults (`true`) | compose `environment:` (`true`) |
| Seeding | manual: `make seed` | automatic on first boot (`SEED_DEMO=1`) |
| Admin user | `make superuser` | `docker compose exec api python manage.py createsuperuser` |
| Code changes | `make run` auto-reloads | re-run `make up` to rebuild (see note) |

> Developing against Docker: code is baked into the image and gunicorn runs
> without `--reload`, so changes to templates, Python, or `.env` need `make up`
> to rebuild and recreate the container — a plain `docker compose restart` will
> not pick them up. For a fast edit loop, prefer Option A.

## Authentication (both modes)

Full design in [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md); the essentials:

- **Demo is open by default.** With `DEMO_OPEN_API=true` (the default in both
  modes) the seven diagram endpoints are reachable without a token, so a bare
  `curl` satisfies the acceptance criteria. It is logged loudly at startup and
  **must be `false` in any real deployment** — the locked-down path is proven by
  `tests/test_permissions.py`.
- **Real auth is JWT** (`djangorestframework-simplejwt`). Obtain a token, then
  send it as a Bearer header:

```bash
# obtain {access, refresh}
ACCESS=$(curl -sX POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"staff@demo.local","password":"demo-pass-123"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access"])')

# call a protected endpoint with the token
curl -s http://127.0.0.1:8000/api/v1/auth/me/ -H "Authorization: Bearer $ACCESS"
```

- **Demo logins** (password `demo-pass-123`): `staff@demo.local`,
  `agent@demo.local`, `customer@demo.local`. They exist after seeding — manual
  (`make seed`) in Local, automatic on first boot in Docker.
- **Roles.** Staff and agents see every customer and policy; a customer sees
  only its own records (a foreign record returns `404`, not `403`).

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

You can also walk all seven steps in the browser at `/` (the single-file demo
client), or explore them interactively at `/api/v1/docs/` (Swagger) and
`/api/v1/redoc/` (ReDoc). The Django admin is at `/admin/`.

## Testing & quality

```bash
make test        # full suite + coverage gate (fail-under 90)
make lint        # ruff
make format      # ruff format + --fix
```

`make test` needs no Docker — it runs on in-memory SQLite by default; CI
additionally runs the whole suite against PostgreSQL. The rating engine, the
policy state machine and the payment service are held at **100%** coverage — the
parts where a bug costs money. Tests live beside the code they cover; only
cross-app end-to-end tests live in `tests/`.

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
