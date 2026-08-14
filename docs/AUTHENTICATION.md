# Authentication & Authorisation

This document explains how identity and access control work in the API and what
a production deployment would add. See [REQUIREMENTS.md](REQUIREMENTS.md) §9 and
[adr/0008-single-user-and-demo-mode.md](adr/0008-single-user-and-demo-mode.md).

## Model

- **One credential store.** A single custom `accounts.User` (email login) with a
  `role` discriminator: `staff`, `agent`, `customer`.
- **Customers are separate business records.** `customers.Customer` is linked to
  a `User` by a nullable `OneToOne` — most insured customers never log in.

| | Staff / agent | Customer |
|---|---|---|
| Created by | admin / `createsuperuser` / IdP | self-registration or agent invite |
| Sees | all customers & policies; Django admin | only its own customer and policies |
| Can create customers | yes | no |
| Can quote / accept / pay | for anyone | only for itself |

## Tokens (JWT, `djangorestframework-simplejwt`)

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/auth/token/` | obtain `{access, refresh}` (throttled 5/min) |
| `POST /api/v1/auth/token/refresh/` | rotate; the presented refresh is blacklisted |
| `POST /api/v1/auth/token/verify/` | verify an access token |
| `POST /api/v1/auth/logout/` | blacklist a refresh token (genuine revocation) |
| `GET /api/v1/auth/me/` | current principal: `id`, `email`, `role`, `customer_id` |

Access tokens live 15 minutes, refresh tokens 7 days, with
`ROTATE_REFRESH_TOKENS` and `BLACKLIST_AFTER_ROTATION` on.

## Authorisation

- **Deny by default.** Global `DemoOrAuthenticated`; `DemoOrStaff` on customer
  creation. `/me/` is always `IsAuthenticated`.
- **404, not 403, for scoping.** A customer principal's `get_queryset` is
  narrowed to its own records, so someone else's policy is reported as *not
  found* — no existence leakage.
- **`DEMO_OPEN_API`.** When true (the default, for the demo) anonymous callers
  reach the diagram endpoints; it is logged loudly at startup. The permission
  matrix is tested in **both** modes (`tests/test_permissions.py`), so the locked
  configuration is proven, not assumed. Set `DEMO_OPEN_API=false` for anything
  real.

## Demo login

`make seed` (→ `seed_demo`) creates `staff@demo.local`, `agent@demo.local`,
`customer@demo.local` (password `demo-pass-123`), with the customer principal
linked to a real `Customer`.

## What production would add

SSO / OIDC for staff and MFA/TOTP; email-OTP or magic-link for customers;
`django-axes` (or equivalent) lockouts on repeated failures; field-level PII
permissions and an access audit log; service-to-service mTLS or API keys;
short-lived tokens with a rotating signing key; and CORS restricted to known
origins.
