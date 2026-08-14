# 0002. One overloaded POST /quote/, via an explicit dispatcher

- Status: accepted
- Date: 2026-08-15

## Context

The sequence diagram posts to the same `POST /api/v1/quote/` three times to do
three different things: create (`customer_id`+`type`), accept (`quote_id`+
`status: "accepted"`) and pay (`quote_id`+`status: "active"`) — REQUIREMENTS 2.1
steps 2-4, D1. A literal reading gives one endpoint with three behaviours, which
is not how REST is usually shaped and can hide intent.

## Decision

Implement the diagram literally so it replays 1:1, but dispatch explicitly: the
view inspects which keys are present and routes to a create / accept / pay
handler, each backed by a narrow `StrictFieldsMixin` serializer. In parallel,
expose clean REST aliases — `POST /quotes/`, `POST /quotes/<id>/accept/`,
`POST /quotes/<id>/pay/` — that call the *same* handlers. Every route is
registered with and without a trailing slash.

## Consequences

- The reviewer can copy any line off the diagram (either slash spelling) and it
  works; a parity test asserts the RPC path and the REST aliases produce the
  same result.
- Ambiguous (`create`+`transition` keys together) and unrecognised payloads get
  a helpful 400; an unsupported `status` is a 400; unknown ids are 404; an
  illegal move is a 409. Affects REQ-P2-1, and pairs with ADR-0004.
