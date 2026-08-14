# 0001. Keep the RPC-style create_customer path, add a REST alias

- Status: accepted
- Date: 2026-08-15

## Context

The brief and the sequence diagram both specify `POST /api/v1/create_customer/`
(REQUIREMENTS 2.1), an RPC-style path in an otherwise resource-oriented API. The
acceptance criteria are written against that literal path, but a reviewer used to
REST would expect `POST /api/v1/customers/`. The diagram also writes step 1
without a trailing slash (`api/v1/create_customer`), and Django's `APPEND_SLASH`
cannot redirect a `POST` without discarding its body.

## Decision

Expose `POST /api/v1/create_customer/` as the primary, tested, documented
contract, and additionally expose `POST /api/v1/customers/` as a REST alias
served by the same view (ENH-01). Register both routes in trailing-slash and
slashless form so either spelling from the diagram works verbatim.

## Consequences

- The acceptance criteria pass exactly as written, and REST-oriented clients get
  a familiar path — both delegate to one `CreateCustomerView`, so there is a
  single code path and one serializer to validate.
- Four route spellings are covered by a parametrized test
  (`apps/customers/tests/test_api.py`).
- `/customers/` becomes a `ListCreate` surface in Phase 8 (search); the create
  behaviour documented here is unchanged.
