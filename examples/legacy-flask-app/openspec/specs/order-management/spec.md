## Purpose

Let clients create and retrieve orders against the demo app. Each order is
assigned a server-generated numeric id and starts in a `pending` status.

<!-- [GAP: README only lists "orders" as a feature; intended order lifecycle
     (e.g. transitions from `pending` to other statuses) is not described
     anywhere — confirm whether `pending` is a placeholder or the only state.] -->

## Requirements

### Requirement: Create order via POST
The system SHALL expose `POST /orders` that accepts a JSON body with at least
an `item` field, assigns a unique numeric id, persists the order, and returns
HTTP 201 with the created order.

**Source:** orders.py:8-17, app.py:7

#### Scenario: Valid create
- **GIVEN** the server has issued ids up to N
- **WHEN** the client POSTs `{"item": "widget"}` to `/orders`
- **THEN** the response is HTTP 201 with body `{"id": N+1, "item": "widget", "status": "pending"}`
- **AND** the order is retrievable via `GET /orders/<id>`

#### Scenario: Missing item field
- **GIVEN** any request body
- **WHEN** the client POSTs to `/orders` without an `item` key
- **THEN** the response is HTTP 400 with body `{"error": "item required"}`

#### Scenario: Missing JSON body
- **GIVEN** no JSON body or a non-JSON body
- **WHEN** the client POSTs to `/orders`
- **THEN** the response is HTTP 400 with body `{"error": "item required"}`  <!-- [GAP: behaviour follows from `request.get_json() or {}`; not explicitly specified] -->

### Requirement: Order ids are monotonically increasing integers starting at 1
The system SHALL assign each new order a server-generated integer id, starting
at 1 and incrementing by 1 for each subsequent successful create.

**Source:** orders.py:5, orders.py:14-16

#### Scenario: Sequential ids
- **GIVEN** the process has just started with no orders
- **WHEN** three orders are created back-to-back
- **THEN** their ids are 1, 2, and 3  <!-- [GAP: behaviour inferred from in-process counter; not robust against restarts or concurrent workers] -->

### Requirement: Retrieve order by id
The system SHALL expose `GET /orders/<int:order_id>` that returns the JSON
order for an existing id with HTTP 200, or HTTP 404 if no such order exists.

**Source:** orders.py:20-25

#### Scenario: Existing order
- **GIVEN** an order with id 1 has been created
- **WHEN** the client GETs `/orders/1`
- **THEN** the response is HTTP 200 with the order body

#### Scenario: Unknown id
- **GIVEN** no order with id 999 exists
- **WHEN** the client GETs `/orders/999`
- **THEN** the response is HTTP 404 with body `{"error": "not found"}`

#### Scenario: Non-integer id
- **GIVEN** any request
- **WHEN** the client GETs `/orders/abc`
- **THEN** the route does not match and Flask's default 404 is returned  <!-- [GAP: routing-level behaviour, not handled explicitly] -->

### Requirement: Orders persist for the lifetime of the process only
The system MAY store orders in an in-memory map that is lost when the process
restarts.

**Source:** orders.py:4

#### Scenario: Restart loses state
- **GIVEN** orders have been created
- **WHEN** the app process restarts
- **THEN** previously created orders are no longer retrievable  <!-- [GAP: acceptable for a demo; confirm whether a real backing store is in scope] -->

<!-- [GAP: no authentication/authorization is enforced — the spec does NOT
     require that callers be authenticated to create or read orders. Confirm
     whether `/orders` is meant to be public or require the `user-auth` token.] -->

<!-- __inferspec_meta__: {"hash": "88bc2a83afb7e8209a967bc8902e78f12f304f14a23440bb3e4aecf16d87684e", "scan_ts": "2026-05-20T08:34:23Z", "version": "0.1"} -->
