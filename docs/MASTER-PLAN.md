# Democrance Technical Test — TDD Master Plan

Version: 1.0
Date: 2026-08-13
Companion to: [REQUIREMENTS.md](REQUIREMENTS.md) (the *what and why*; this is the *in what order, which
test first*)
Target: complete within 3 days of receipt

---

## 1. Method

Strict red-green-refactor, enforced by the commit history so the process is visible to the reviewer —
which the brief explicitly says it is looking for.

For every unit of behaviour:

1. **RED** — write the test(s) first. Run them. Confirm they fail *for the intended reason* (not an
   import error masquerading as a failure). Commit as `test(scope): ...`.
2. **GREEN** — write the simplest implementation that passes. Run the whole suite. Commit as
   `feat(scope): ...` or `fix(scope): ...`.
3. **REFACTOR** — improve naming, extract, remove duplication, add type hints. Suite stays green.
   Commit as `refactor(scope): ...` only when there is something real to say.

Rules held throughout:

- No production code is written without a failing test demanding it.
- A bug found manually gets a failing regression test *before* the fix.
- Tests assert behaviour and contracts, not implementation details.
- The suite must stay fast: SQLite in memory locally, PostgreSQL in CI.
- No mocking of the ORM. The only simulated thing is the payment gateway, because it does not exist.

### 1.1 Test pyramid for this project

- **Unit (no DB where possible)** — rating engine, `FlexibleDateField`, age calculation, state
  transition table, payment simulator.
- **Model/integration (DB)** — constraints, indexes used, cascade/PROTECT behaviour, immutability of
  history rows.
- **Serializer** — input validation matrix, read-only enforcement, output shape.
- **API** — status codes, payload contracts, error codes, permission matrix, query counts.
- **Admin** — the two stated acceptance criteria, driven through Django's test client.
- **End-to-end** — one test that replays all seven sequence-diagram steps in order.

### 1.2 Test-design decisions made up front (to avoid rework)

These are deliberate, because getting them wrong means rewriting dozens of tests in Phase 9:

- **All API tests use an auth-aware `api_client` fixture from Phase 2 onward**, even before auth exists.
  When JWT lands, only the fixture changes — not the tests. Fixtures: `anon_client`, `staff_client`,
  `agent_client`, `customer_client(customer)`.
- **`time-machine` pins "today" to `2026-08-13`** in any test involving age, expiry, or `dob`, so
  age-band tests do not rot as real time passes.
- **`factory_boy` factories** (`CustomerFactory`, `ProductTypeFactory`, `RatingRuleFactory`,
  `PolicyFactory`, `UserFactory`) live in each app's `tests/factories.py` and are registered in
  `tests/conftest.py`. Factories create *valid minimum* objects; each test makes its own deviation
  explicit.
- **Boundary values are `pytest.mark.parametrize`d**, not copy-pasted — age bands, state transitions,
  and the permission matrix are all table-driven.
- **The permission matrix runs twice**, with `DEMO_OPEN_API` true and false, so the secure
  configuration is proven rather than assumed.

### 1.3 Commit convention

Conventional Commits with a scope, small and frequent. An honest example of the intended rhythm:

```
chore(repo): scaffold django project with split settings and pytest
test(customers): expect POST /api/v1/create_customer/ to persist a customer
feat(customers): add Customer model and create_customer endpoint
test(customers): reject future dob and out-of-range ages
feat(customers): validate dob range at the serializer boundary
refactor(common): extract FlexibleDateField for DD-MM-YYYY and ISO input
docs(adr): record why create_customer keeps its RPC-style path
```

---

## 2. Phase plan

Twelve phases. Each states the requirement IDs it satisfies, the tests written **first**, the
implementation that follows, and a hard exit criterion. Phases are ordered so that nothing has to be
retrofitted — most importantly the custom user model lands before any other migration, and auth-aware
test fixtures exist before the first endpoint test.

### Phase 0 — Walking skeleton and tooling

Satisfies: REQ-P1-1, REQ-P1-7, `ENH-10`

RED

- `tests/test_smoke.py::test_healthz_returns_ok`
- `tests/test_smoke.py::test_settings_fall_back_to_sqlite_without_database_url`

GREEN

- `git init`; `.gitignore`; `requirements/{base,dev}.txt` with the pinned versions from
  REQUIREMENTS.md §5.4
- `django-admin startproject config .`; split settings `config/settings/{base,dev,test,prod}.py`;
  `dj-database-url` + `python-decouple`; `.env.example` with `DEMO_OPEN_API=true`
- `pyproject.toml`: ruff, pytest (`DJANGO_SETTINGS_MODULE=config.settings.test`), coverage
  (`fail_under=90`)
- `Makefile`: `install`, `run`, `test`, `lint`, `format`, `migrate`, `seed`, `superuser`, `up`, `down`,
  `demo`
- `/healthz/` view with a DB round-trip; `.pre-commit-config.yaml`; `.github/workflows/ci.yml`

Exit: `make test` green, `make run` serves, `make lint` clean, first commits pushed.

### Phase 1 — Custom user model (before anything else migrates)

Satisfies: foundation for REQ-P4-2

RED — `apps/accounts/tests/test_models.py`

- `test_create_user_normalises_email_and_hashes_password`
- `test_create_user_without_email_raises`
- `test_default_role_is_customer`
- `test_create_superuser_sets_staff_and_superuser_flags`
- `test_str_returns_email`

GREEN — `apps.accounts` with `User(AbstractBaseUser, PermissionsMixin)`, email as `USERNAME_FIELD`,
`role` choices, custom manager, `AUTH_USER_MODEL = "accounts.User"`, initial migration.

Exit: `migrate` clean on an empty database; no other app has migrated yet.

### Phase 2 — Part 1: customer creation

Satisfies: REQ-P1-2, REQ-P1-3, REQ-P1-4, REQ-P1-6, D2

RED

- `apps/common/tests/test_fields.py` — `FlexibleDateField`: parses `25-06-1991`, parses `1991-06-25`,
  rejects `1991-25-06` / `31-02-1991` / `"yesterday"` / `""`, renders `25-06-1991` on output
- `apps/customers/tests/test_models.py` — `age_at` on the birthday, the day before, and the day after;
  leap-year `dob` (29-02); future `dob` rejected; age below 18 and above 100 rejected; `__str__`
- `apps/customers/tests/test_serializers.py` — required fields; whitespace stripped; unknown fields
  rejected; `age` is read-only and computed
- `apps/customers/tests/test_api.py` — `test_create_customer_with_brief_payload_returns_201_and_persists`
  (the brief's exact JSON), response contains `id` + `dob` as `DD-MM-YYYY`, `400` matrix with the
  uniform error envelope, wrong method returns `405`
- `apps/customers/tests/test_admin.py` — customer is listed, searchable by surname, and its change page
  renders (REQ-P1-6)

GREEN — `apps.common` (`TimeStampedModel`, `FlexibleDateField`, exception handler, error codes,
pagination); `apps.customers` (model + migration, serializer, view wired to **both**
`/api/v1/create_customer/` and `/api/v1/customers/`, admin, factory).

Exit: the brief's `curl` creates a customer visible in admin; acceptance criterion 1 demonstrably met.

Commits: `test(common)` -> `feat(common)` -> `test(customers)` -> `feat(customers)` ->
`docs(adr): 0001, 0005`.

### Phase 3 — Products and the rating engine (pure domain)

Satisfies: REQ-P2-3, D6, `ENH-02`, `ENH-03`

RED — `apps/products/tests/`

- `test_rating.py::test_brief_example_prices_at_200` — Ben Stokes, `cover 200000`, `2026-08-13` ->
  `Decimal("200.00")`
- `test_rating.py::test_age_band_boundaries` — parametrized over 17/18, 25/26, 30/31, 40/41, 70/71
- `test_rating.py::test_min_premium_is_applied_for_small_cover`
- `test_rating.py::test_rounding_is_half_up_to_two_places`
- `test_rating.py::test_missing_band_raises_no_applicable_rate`
- `test_rating.py::test_inactive_product_raises`
- `test_rating.py::test_cover_outside_product_limits_raises`
- `test_rating.py::test_rule_selected_by_as_of_date_respects_valid_from_to`
- `test_models.py::test_overlapping_active_bands_are_rejected`
- `test_models.py::test_age_band_min_greater_than_max_violates_db_constraint`
- `test_seed.py::test_seed_migration_loads_personal_accident_rates`

GREEN — `ProductType`, `RatingRule` (+ `CheckConstraint`, `clean()` overlap validation), pure
`rating.calculate_premium(product, age, cover, as_of)` returning premium plus the rule used, seed data
migration, admin.

Exit: rating engine at 100% coverage; the brief's own example reproduces without special-casing.

### Phase 4 — Policy model, state machine, quote services (still no HTTP)

Satisfies: REQ-P2-2, REQ-P2-5, REQ-P2-7, D7, `ENH-04`, `ENH-06`

RED — `apps/policies/tests/`

- `test_state_machine.py::test_allowed_transitions` — parametrized over the full legal table
- `test_state_machine.py::test_forbidden_transitions_raise` — parametrized, including
  `quoted -> active` (skipping acceptance) and `active -> active`
- `test_transitions.py::test_transition_row_records_from_to_actor_source_and_metadata`
- `test_transitions.py::test_transition_rows_are_immutable_once_saved`
- `test_transitions.py::test_failed_transition_writes_no_history_row`
- `test_services.py::test_create_quote_records_new_then_quoted` (the two-step narrative)
- `test_services.py::test_create_quote_sets_premium_cover_rated_age_and_expiry`
- `test_services.py::test_create_quote_defaults_cover_to_product_default`
- `test_services.py::test_accept_quote_sets_accepted_at`
- `test_services.py::test_accept_expired_quote_is_refused`
- `test_services.py::test_activate_requires_accepted_state`
- `test_services.py::test_concurrent_activation_binds_only_once` (row lock, `ENH-06a`)
- `test_models.py::test_quote_reference_is_unique_and_human_readable`
- `test_models.py::test_customer_deletion_is_protected_while_policies_exist`

GREEN — `Policy`, `PolicyStateTransition`, `state_machine.py` (declarative transition table +
`InvalidStateTransition`), `services.py` (`create_quote`, `accept_quote`, `activate_policy`, all
`transaction.atomic()` + `select_for_update()`), reference generator, factories.

Exit: the whole lifecycle is exercisable from a Django shell with full history, before any endpoint
exists. State machine at 100% coverage.

### Phase 5 — Payment simulation

Satisfies: REQ-P2-4, `ENH-05`

RED — `apps/payments/tests/test_services.py`

- `test_simulated_card_payment_succeeds_and_binds_policy`
- `test_invoice_method_leaves_payment_pending_but_still_binds_policy`
- `test_payment_refused_when_policy_not_accepted`
- `test_replayed_idempotency_key_returns_original_payment_without_double_charging`
- `test_same_idempotency_key_with_different_body_conflicts`
- `test_payment_amount_matches_policy_premium_and_currency`

GREEN — `Payment` model, `simulate_payment()`, wiring into `activate_policy` so binding and settlement
are one atomic unit, admin (read-only).

Exit: both payment paths from the brief ("simulate payment" / "invoiced later") are covered.

### Phase 6 — The `/api/v1/quote/` endpoint and REST aliases

Satisfies: REQ-P2-1, D1, ADR-0002, ADR-0004

RED — `apps/policies/tests/test_quote_api.py`

- `test_create_quote_from_diagram_payload_returns_201` — exactly `{"customer_id": 1, "type": "personal-accident"}`
- `test_accept_quote_from_diagram_payload_returns_200` — `{"quote_id": 1, "status": "accepted"}`
- `test_pay_quote_from_diagram_payload_returns_200` — `{"quote_id": 1, "status": "active"}`
- `test_ambiguous_payload_returns_400_with_guidance` (both `customer_id` and `quote_id`, or neither)
- `test_unsupported_status_value_returns_400` (for example `status: "cancelled"`)
- `test_client_supplied_premium_is_rejected` (ADR-0004)
- `test_cover_outside_product_limits_returns_400`
- `test_unknown_customer_or_quote_returns_404`
- `test_illegal_transition_returns_409_with_error_code`
- `test_rest_aliases_produce_identical_results` — parametrized over the diagram path and
  `/quotes/<id>/accept|pay/`

GREEN — `QuoteRequestSerializer` dispatcher (chooses the create/accept/pay sub-serializer by keys
present, with an explicit error when it cannot decide), one thin view calling one service function per
branch, URL wiring for both styles.

Exit: diagram steps 2, 3 and 4 replay exactly as drawn.

### Phase 7 — Policy list, detail and history endpoints

Satisfies: REQ-P2-5, REQ-P3-4, diagram steps 5–7, `ENH-12`

RED — `apps/policies/tests/test_policy_api.py`

- `test_list_policies_filtered_by_customer_id`
- `test_list_policies_is_paginated_and_ordered_newest_first`
- `test_list_policies_does_not_n_plus_one` (`django_assert_num_queries`)
- `test_policy_detail_includes_customer_rating_inputs_and_payment`
- `test_policy_detail_404_for_unknown_id`
- `test_history_returns_full_ordered_narrative` — asserts exactly
  `[None->new, new->quoted, quoted->accepted, accepted->active]`
- `test_history_of_fresh_quote_shows_only_new_and_quoted`

GREEN — list/detail/history views, serializers with `select_related` / `prefetch_related`, filterset,
pagination class.

Exit: all seven diagram interactions exist and are individually tested.

### Phase 8 — Part 3: search

Satisfies: REQ-P3-1, REQ-P3-2, REQ-P3-3, REQ-P3-4, D8

RED — `apps/customers/tests/test_search_api.py`, `apps/search/tests/test_unified_search.py`

- `test_search_customers_by_partial_last_name_case_insensitively`
- `test_search_customers_by_first_name`
- `test_free_text_q_matches_either_name`
- `test_search_customers_by_dob_in_both_accepted_formats` (parametrized)
- `test_search_customers_by_policy_type_returns_only_holders_of_that_type`
- `test_filters_combine_with_and_semantics`
- `test_policies_filterable_by_type_and_state`
- `test_no_matches_returns_empty_paginated_result_not_404`
- `test_unified_search_returns_both_entities_with_counts`
- `test_unified_search_entity_parameter_narrows_results`
- `test_malicious_input_is_safely_parameterised` (quote/semicolon payload returns empty, not an error)

GREEN — `CustomerFilterSet`, `PolicyFilterSet` (`django-filter`), `q` handling, `apps.search` unified
view with a documented result envelope.

Exit: every search path named in Part 3 is covered by a test.

### Phase 9 — Part 4: authentication and authorisation

Satisfies: REQ-P4-2, D3, D4, `ENH-09`

RED — `apps/accounts/tests/`

- `test_auth_api.py::test_token_obtain_returns_access_and_refresh`
- `test_auth_api.py::test_token_obtain_with_bad_credentials_returns_401_uniform_error`
- `test_auth_api.py::test_token_refresh_rotates_and_blacklists_previous`
- `test_auth_api.py::test_logout_blacklists_refresh_token_and_prevents_reuse`
- `test_auth_api.py::test_me_returns_role_and_linked_customer_id`
- `test_auth_api.py::test_token_endpoint_is_throttled`
- `test_permissions.py::test_permission_matrix` — parametrized over
  (principal in {anonymous, customer, agent, staff}) x (all endpoints) x (`DEMO_OPEN_API` in
  {true, false}) with expected status codes
- `test_permissions.py::test_customer_cannot_read_another_customers_policy_and_gets_404`
- `test_permissions.py::test_customer_cannot_create_customers`
- `test_permissions.py::test_customer_can_quote_accept_and_pay_only_for_itself`
- `test_permissions.py::test_demo_mode_flag_logs_a_warning_on_startup`

GREEN — `simplejwt` configuration (rotation + blacklist), auth views, `IsStaff`,
`IsStaffOrOwningCustomer`, `DemoOrAuthenticated`, queryset narrowing in every list/detail view, a
`seed_demo` management command creating staff/agent/customer users plus the brief's sample data.

REFACTOR — swap the `api_client` fixtures to attach real JWTs; no test bodies change (see §1.2).

Exit: the full matrix passes in both modes; `docs/AUTHENTICATION.md` drafted alongside.

### Phase 10 — OpenAPI, admin polish, demo SPA, documentation

Satisfies: REQ-P1-5, REQ-P1-6, REQ-P2-6, REQ-P4-1, `ENH-07`, `ENH-11`

RED

- `tests/test_schema.py::test_openapi_schema_generates_without_warnings`
- `tests/test_schema.py::test_swagger_ui_and_redoc_render`
- `apps/policies/tests/test_admin.py::test_policy_changelist_shows_linked_customer` (REQ-P2-6)
- `apps/policies/tests/test_admin.py::test_transition_history_inline_is_read_only`
- `apps/policies/tests/test_admin.py::test_admin_bind_action_uses_service_layer_and_records_admin_source`
- `apps/policies/tests/test_admin.py::test_state_field_is_not_directly_editable`
- `apps/web/tests/test_demo_client.py::test_root_serves_single_page_client`

GREEN — `drf-spectacular` settings, per-view `extend_schema` with request/response examples taken
straight from the diagram; admin classes and actions per REQUIREMENTS.md §10; `apps.web` template +
vanilla-JS client (login, then the seven calls in order, each showing request and response JSON);
`docs/API.md`, `docs/AUTHENTICATION.md`, `docs/adr/0001–0008`, `README.md`.

Exit: a reviewer can complete the entire flow in a browser with no tooling, and both admin acceptance
criteria are automated.

### Phase 11 — End-to-end acceptance, Docker, CI, hardening

Satisfies: REQ-P1-5, REQ-P1-7, `ENH-10`, `ENH-13`

RED

- `tests/e2e/test_sequence_diagram_flow.py::test_full_diagram_flow` — one test walking all seven steps
  in order and asserting the final state plus the four-entry history
- `tests/e2e/test_acceptance_criteria.py::test_part1_customer_visible_in_admin_after_post`
- `tests/e2e/test_acceptance_criteria.py::test_part2_policy_linked_to_correct_customer_in_admin`
- `tests/test_migrations.py::test_no_missing_migrations` (`makemigrations --check --dry-run`)

GREEN — `Dockerfile` (multi-stage, non-root, `whitenoise`, `gunicorn`), `docker-compose.yml` (api +
Postgres + healthchecks), `make demo` (seed then run the e2e flow verbosely), request-ID middleware and
structured logging, `prod` settings hardening, CI matrix on SQLite and PostgreSQL with the coverage
gate.

Exit: `git clone && make up && make demo` works from cold on a machine with only Docker.

### Phase 12 — Review pass and handover

- Re-read REQUIREMENTS.md §4 line by line and tick every REQ ID against a named test.
- `make lint && make test` from a clean checkout; confirm coverage gates.
- Read the git log end to end: does it tell an honest TDD story?
- README final pass: quickstart, the exact acceptance-criteria commands, design summary, the deviations
  from the brief and why, what was deliberately left out, and how long each part took.
- Optional (low cost, good signal): a short `docs/DEMO.md` walkthrough of what to click in admin.

---

## 3. Schedule (3 calendar days)

- **Day 1 — foundations and domain (~6h):** Phases 0–4. Ends with the full quote lifecycle working from
  the shell, with history, fully unit-tested.
- **Day 2 — the API surface (~6h):** Phases 5–9. Ends with all seven endpoints plus search and auth
  green, permission matrix passing in both modes.
- **Day 3 — reviewer experience and hardening (~5h):** Phases 10–12. Ends with Swagger UI, the demo SPA,
  Docker, CI, docs, and a rehearsed acceptance walkthrough.

Buffer: the SPA (`ENH-11`) and the concurrency test (`ENH-06a`) are the two items that can slip to a
follow-up commit without touching any stated requirement. Nothing in Parts 1–4 is in the buffer.

---

## 4. Risk register

- **Overloaded `POST /quote/` becomes ambiguous.** Mitigated by an explicit dispatcher with a helpful
  400, parity tests against the REST aliases, and ADR-0002.
- **`dob` format misread as US.** Mitigated by accepting both formats, rendering `DD-MM-YYYY`, and
  rejecting impossible dates outright.
- **Custom user model added too late.** Mitigated by making it Phase 1, before any other migration.
- **Auth retrofit invalidating earlier tests.** Mitigated by auth-aware client fixtures from Phase 2.
- **Age-dependent tests rotting over time.** Mitigated by `time-machine` pinning the clock.
- **Demo-open mode mistaken for the intended production posture.** Mitigated by a startup warning, a
  README callout, and tests that prove the locked-down mode.
- **Scope creep into claims/renewals.** Mitigated by the explicit out-of-scope list in
  REQUIREMENTS.md §12.

---

## 5. Reviewer quickstart (to be mirrored in README.md)

```bash
git clone <repo> && cd democrance-insurance-api
cp .env.example .env

# Option A: Docker (PostgreSQL)
make up && make seed && make demo

# Option B: no Docker (SQLite fallback)
make install && make migrate && make seed && make run

# Verify Part 1 exactly as the acceptance criteria describe
curl -X POST http://localhost:8000/api/v1/create_customer/ \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Ben", "last_name": "Stokes", "dob": "25-06-1991"}'

# Then: http://localhost:8000/admin/  (customer + policy with correct linkage)
#       http://localhost:8000/api/v1/docs/  (Swagger UI)
#       http://localhost:8000/  (click through all seven diagram steps)
make test   # full suite with coverage gate
```
