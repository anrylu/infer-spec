## Purpose

Expose a lightweight liveness endpoint so operators and load balancers can
confirm the demo app is up.

<!-- [GAP: README mentions "a health check" but no SLO, no documented consumer
     (e.g., k8s probe, LB), and no readiness vs. liveness distinction. Confirm
     intended use.] -->

## Requirements

### Requirement: Health endpoint returns OK
The system SHALL expose `GET /health` that returns HTTP 200 with body
`{"status": "ok"}` whenever the process is serving requests.

**Source:** app.py:10-12

#### Scenario: Healthy response
- **GIVEN** the app process is running and accepting connections
- **WHEN** the client GETs `/health`
- **THEN** the response is HTTP 200 with body `{"status": "ok"}`

#### Scenario: Health does not require authentication
- **GIVEN** an unauthenticated client
- **WHEN** the client GETs `/health`
- **THEN** the response is HTTP 200  <!-- [GAP: no auth check is present in code; confirm this is intentional] -->

### Requirement: Health endpoint never reports unhealthy
The endpoint MUST always succeed when the process can handle the request; it
does not perform downstream dependency checks.

**Source:** app.py:10-12

#### Scenario: No dependency probing
- **GIVEN** any external dependency state (the demo has none)
- **WHEN** the client GETs `/health`
- **THEN** the response is still HTTP 200  <!-- [GAP: acceptable for a static liveness check; confirm whether readiness semantics are wanted later] -->

<!-- __inferspec_meta__: {"hash": "3f28919a8621dc87e8a3b5cfa6324590f6ddf84c519701d3aa17c677a264d4c7", "scan_ts": "2026-05-20T08:34:23Z", "version": "0.1"} -->
