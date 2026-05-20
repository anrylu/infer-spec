## Purpose

Provide password-based login for the demo app's known users and issue a token
that downstream capabilities can use to identify the caller. The capability
also throttles repeated bad-password attempts so a single account cannot be
brute-forced from one source.

This capability is **demo-only** — it does not claim a production-grade threat
model. Token issuance, rate-limit persistence, and user storage are all
intentional placeholders meant to illustrate the surface, not to harden it.
Production deployment must add real session handling (opaque or signed
tokens), persistent rate-limit state, and a real user store.

## Requirements

### Requirement: Login endpoint accepts JSON credentials
The system SHALL expose `POST /auth/login` that accepts a JSON body with
`user` and `password` fields and, on success, returns HTTP 200 with a JSON
body containing a token identifier. The current token scheme `session-<user>`
is a deliberate demo placeholder — production deployment MUST replace it with
an opaque session id or signed token.

**Source:** auth.py:18-31, app.py:6

#### Scenario: Valid credentials
- **GIVEN** a known user `alice` with the expected password
- **WHEN** the client POSTs `{"user": "alice", "password": "secret123"}` to `/auth/login`
- **THEN** the response is HTTP 200 with body `{"token": "session-alice"}` (placeholder token format)

#### Scenario: Missing JSON body
- **GIVEN** no JSON body or a non-JSON body is sent
- **WHEN** the client POSTs to `/auth/login`
- **THEN** the request is treated as having empty `user` and `password` and is rejected as bad credentials (intentional — malformed payloads share the bad-credentials response path, no separate 400)

### Requirement: Invalid credentials are rejected with 401
The system SHALL reject any login whose credentials do not match the stored
password for the given user, returning HTTP 401 with body
`{"error": "bad credentials"}`, and SHALL record the failed attempt against
the supplied username. The response for an unknown user SHALL be
indistinguishable from the response for a wrong password — this is an
intentional anti-user-enumeration property.

**Source:** auth.py:27-29

#### Scenario: Wrong password for known user
- **GIVEN** user `alice` exists
- **WHEN** the client POSTs `{"user": "alice", "password": "wrong"}`
- **THEN** the response is HTTP 401 with body `{"error": "bad credentials"}`
- **AND** the failed attempt is recorded against `alice`

#### Scenario: Unknown user
- **GIVEN** no user `mallory` exists
- **WHEN** the client POSTs `{"user": "mallory", "password": "anything"}`
- **THEN** the response is HTTP 401 with body `{"error": "bad credentials"}`
- **AND** the failed attempt is recorded against `mallory` (indistinguishable from a real user's bad-password path)

### Requirement: Per-user rate limiting on failed attempts
The system MUST refuse further login attempts for a user once that user has
accumulated 5 failed attempts within the preceding 60 seconds, returning HTTP
429 until older failures age out of the window.

**Source:** auth.py:9, auth.py:12-15, auth.py:24-25

#### Scenario: Threshold exceeded
- **GIVEN** user `alice` has 5 failed login attempts recorded in the last 60 seconds
- **WHEN** the client POSTs any credentials for `alice` to `/auth/login`
- **THEN** the response is HTTP 429 with body `{"error": "too many attempts"}`

#### Scenario: Failure window slides
- **GIVEN** user `alice` had 5 failed attempts, the oldest of which was more than 60 seconds ago
- **WHEN** the client POSTs credentials for `alice`
- **THEN** the request is processed normally (the aged-out failure does not count)

#### Scenario: Successful login does not reset counter
- **GIVEN** user `alice` has 4 failed attempts within the last 60 seconds
- **WHEN** `alice` logs in successfully
- **THEN** the recorded failures are NOT cleared

#### Scenario: Process restart clears rate-limit state
- **GIVEN** user `alice` has accumulated failed attempts within the window
- **WHEN** the app process restarts
- **THEN** all failure records for `alice` are forgotten (best-effort, in-memory only)

### Requirement: User store is a fixed in-memory map
The system MAY operate from a hardcoded in-memory user/password map for the
demo environment.

**Source:** auth.py:8

#### Scenario: Process restart preserves user list
- **GIVEN** the demo app is restarted
- **WHEN** clients reconnect
- **THEN** the same hardcoded users remain available

<!-- __inferspec_meta__: {"hash": "fd03f55f80102fc30ec2abdabc82dc27c36297b07b9c97bc2bff6230da780155", "scan_ts": "2026-05-20T08:34:23Z", "last_qa_run": "2026-05-20T09:51:54Z", "version": "0.1"} -->
