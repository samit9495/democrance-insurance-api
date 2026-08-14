# Requirement traceability

Every requirement, decision, and enhancement in [REQUIREMENTS.md](REQUIREMENTS.md)
mapped to the named test(s) that prove it. Run any row with, e.g.:

```bash
pytest apps/customers/tests/test_api.py::test_create_customer_with_brief_payload_returns_201_and_persists
```

The full suite is 192 tests; overall line+branch coverage is 96% (gate 90%) and
the rating engine is at 100% (its own gate). Both gates run in CI on SQLite and
PostgreSQL.

## Part 1 — customer creation

| ID | Requirement | Proving test(s) |
|----|-------------|-----------------|
| REQ-P1-1 | Django project runs; `runserver` starts | `tests/test_smoke.py::test_healthz_returns_ok`, `::test_settings_fall_back_to_sqlite_without_database_url` |
| REQ-P1-2 | `POST /api/v1/create_customer/` accepts JSON | `apps/customers/tests/test_api.py::test_create_customer_with_brief_payload_returns_201_and_persists` |
| REQ-P1-3 | `Customer` model with name/dob/id | `apps/customers/tests/test_models.py::test_str_includes_full_name`, `apps/customers/tests/test_serializers.py::test_required_fields_are_enforced` |
| REQ-P1-4 | Brief payload creates a customer | `apps/customers/tests/test_api.py::test_create_customer_with_brief_payload_returns_201_and_persists` |
| REQ-P1-5 | Reproducible executable e2e suite | `tests/e2e/test_full_diagram_flow.py::test_seven_step_diagram_flow`, `tests/e2e/test_acceptance_criteria.py::*` |
| REQ-P1-6 | Customer visible/correct in admin | `apps/customers/tests/test_admin.py::test_customer_is_listed_in_admin`, `::test_customer_change_page_renders`, `::test_customer_is_searchable_by_surname` |
| REQ-P1-7 | Incremental, reviewable git history | `git log` reads test→feat per phase (see README §History); identity audit is samit9495-only |

## Part 2 — quotes, policies, lifecycle

| ID | Requirement | Proving test(s) |
|----|-------------|-----------------|
| REQ-P2-1 | `POST /api/v1/quote/` exists | `apps/policies/tests/test_api_quote.py::test_create_quote_replays_diagram_step_2` |
| REQ-P2-2 | `Policy` model with type/premium/cover/state + customer FK | `apps/policies/tests/test_models.py::test_quote_reference_is_generated_and_unique`, `::test_customer_with_policies_cannot_be_deleted` |
| REQ-P2-3 | Premium derived from age band and cover | `apps/products/tests/test_rating.py::test_brief_example_prices_at_200`, `::test_band_boundaries_select_the_right_rate`, `::test_min_premium_is_applied_as_a_floor`, `::test_rounding_is_half_up_not_bankers` |
| REQ-P2-4 | Accept then bind to active, with payment | `apps/payments/tests/test_services.py::test_card_payment_succeeds_and_binds`, `::test_invoice_payment_is_pending_but_still_binds`, `apps/policies/tests/test_api_quote.py::test_dispatch_replays_diagram_steps_2_to_4` |
| REQ-P2-5 | State history queryable, full ordered progression | `apps/policies/tests/test_api_policies.py::test_history_returns_the_full_four_entry_narrative`, `apps/policies/tests/test_services.py::test_full_lifecycle_records_the_whole_narrative` |
| REQ-P2-6 | Admin shows policy ↔ correct customer | `apps/policies/tests/test_admin.py::test_changelist_shows_the_linked_customer` |
| REQ-P2-7 | Illegal transitions rejected sensibly | `apps/policies/tests/test_api_quote.py::test_paying_an_unaccepted_quote_is_409`, `apps/policies/tests/test_state_machine.py::test_illegal_transitions_are_refused` |

## Part 3 — search

| ID | Requirement | Proving test(s) |
|----|-------------|-----------------|
| REQ-P3-1 | Findable by name (partial, case-insensitive) | `apps/customers/tests/test_search.py::test_partial_case_insensitive_surname`, `::test_partial_first_name`, `::test_free_text_q_spans_either_name` |
| REQ-P3-2 | Findable by `dob` (both formats) | `apps/customers/tests/test_search.py::test_dob_accepts_both_formats` |
| REQ-P3-3 | Customers and policies findable by policy type | `apps/customers/tests/test_search.py::test_filter_by_held_policy_type`, `apps/policies/tests/test_api_policies.py::test_policies_filter_by_type_and_state` |
| REQ-P3-4 | Policies filterable by customer_id/state/type, paginated | `apps/policies/tests/test_api_policies.py::test_list_filters_by_customer_id`, `::test_list_is_paginated_and_newest_first`, `::test_policies_filter_by_type_and_state` |

## Part 4 — authentication and authorisation

| ID | Requirement | Proving test(s) |
|----|-------------|-----------------|
| REQ-P4-1 | Written auth discussion doc | [`docs/AUTHENTICATION.md`](AUTHENTICATION.md) |
| REQ-P4-2 | JWT issue/refresh/verify/logout, roles, scoping | `apps/accounts/tests/test_auth.py::test_token_obtain_returns_access_and_refresh`, `::test_refresh_rotates_and_blacklists_the_old_token`, `::test_logout_blacklists_the_refresh_token`, `::test_me_returns_role_and_linked_customer_id`, `tests/test_permissions.py::*` |

## Decisions (D-series)

| ID | Decision | Proving test(s) |
|----|----------|-----------------|
| D1 | Diagram paths + REST aliases | `apps/policies/tests/test_api_quote.py::test_rest_aliases_accept_and_pay_match_the_rpc_path`, `::test_create_parity_across_aliases_and_slashes` |
| D2 | `dob` DD-MM-YYYY + ISO in, DD-MM-YYYY out | `apps/common/tests/test_fields.py::test_parses_accepted_input_formats`, `::test_renders_ddmmyyyy_on_output` |
| D3 | JWT auth, two principals | `apps/accounts/tests/test_auth.py::*` |
| D4 | `DEMO_OPEN_API` both modes tested | `tests/test_permissions.py::test_anonymous_is_admitted_in_demo_mode`, `::test_anonymous_is_denied_when_locked` |
| D5 | Compose+Postgres and SQLite fallback | `tests/test_smoke.py::test_settings_fall_back_to_sqlite_without_database_url`; CI matrix runs both |
| D6 | DB-driven `RatingRule`, seeded, admin-editable | `apps/products/tests/test_seed.py::test_seed_creates_the_catalogue`, `apps/products/tests/test_admin.py::test_admin_rejects_an_overlapping_rating_band` |
| D7 | Immutable `PolicyStateTransition` via service | `apps/policies/tests/test_models.py::test_transition_is_immutable_after_save` |
| D8 | django-filter params + unified `/search/` | `apps/search/tests/test_search.py::test_search_returns_both_entities_with_counts`, `::test_entity_narrows_the_result` |
| D9 | pytest + factory_boy + coverage gate, TDD | 192 tests; `pyproject.toml` `fail_under=90`; git history is test-first |
| D10 | OpenAPI/Swagger + Makefile | `apps/web/tests/test_web.py::test_interactive_docs_render`; `Makefile` targets |
| D11 | Single static HTML client at `/` | `apps/web/tests/test_web.py::test_demo_spa_is_served_at_the_root` |

## Enhancements (ENH-series)

| ID | Enhancement | Proving test(s) |
|----|-------------|-----------------|
| ENH-01 | REST aliases | `apps/customers/tests/test_api.py::test_all_route_spellings_create_a_customer`, `apps/policies/tests/test_api_quote.py::test_create_parity_across_aliases_and_slashes` |
| ENH-02/02a | `ProductType` catalogue + UUID reference | `apps/products/tests/test_models.py::test_str_methods`, `apps/payments/tests/test_services.py::test_activation_records_the_payment_reference` |
| ENH-03 | Date-versioned rating rules | `apps/products/tests/test_rating.py::test_date_versioned_rule_selection`, `apps/products/tests/test_models.py::test_versioned_bands_in_disjoint_windows_do_not_clash` |
| ENH-04 | Quote expiry enforced on accept | `apps/policies/tests/test_services.py::test_accepting_an_expired_quote_is_refused` |
| ENH-05 | Payment idempotency + invoice path | `apps/payments/tests/test_services.py::test_idempotent_replay_returns_the_same_payment`, `::test_same_key_with_a_different_body_conflicts`, `::test_invoice_payment_is_pending_but_still_binds` |
| ENH-06/06a | Immutable audit trail, row-locked bind-once | `apps/policies/tests/test_services.py::test_activating_twice_binds_only_once`, `::test_activate_requires_accepted_and_writes_no_row_on_failure` |
| ENH-07 | OpenAPI/Swagger/ReDoc | `apps/web/tests/test_web.py::test_schema_generates_without_warnings`, `::test_interactive_docs_render` |
| ENH-08 | Unified `/search/` | `apps/search/tests/test_search.py::test_search_returns_both_entities_with_counts` |
| ENH-09 | Full JWT + object scoping | `tests/test_permissions.py::test_customer_gets_404_not_403_for_a_foreign_policy`, `::test_customer_cannot_create_customers` |
| ENH-10 | Docker, Makefile, CI, SQLite fallback | `tests/test_migrations.py::test_no_missing_migrations`; verified `docker compose up` cold start |
| ENH-11 | Single-file SPA walking the sequence | `apps/web/tests/test_web.py::test_demo_spa_is_served_at_the_root` |
| ENH-12 | Query-count tests + coverage gate | `apps/policies/tests/test_api_policies.py::test_list_has_no_n_plus_one` |
| ENH-13 | Structured logging + request IDs | `tests/e2e/test_full_diagram_flow.py::test_every_response_echoes_a_request_id`, `::test_request_id_is_minted_when_absent` |
| ENH-13a | `/healthz/` + container healthcheck | `tests/test_smoke.py::test_healthz_returns_ok`, `::test_healthz_reports_error_when_database_is_unreachable` |

## Deliberately out of scope

`ENH-14` (dedupe/GDPR erasure), `ENH-15` (renewals/endorsements/claims),
`ENH-16` (Celery async), `ENH-17` (SSO/MFA/lockouts), `ENH-18` (multi-currency
FX/reinsurance), `ENH-19` (real gateway). These are argued in REQUIREMENTS.md §11
and, where relevant, in [AUTHENTICATION.md](AUTHENTICATION.md).
