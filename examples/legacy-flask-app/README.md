# Legacy Flask Demo

Tiny Flask app used as InferSpec's reference target. Three "capabilities":
authentication (`auth.py`), orders (`orders.py`), and a health check (`app.py`).

## Worked example

`openspec/specs/` in this directory contains the actual output from running
the InferSpec skills against this code — committed so newcomers can see what
the tooling produces without running it themselves.

| Spec | Produced by | State |
|---|---|---|
| `openspec/specs/user-auth/spec.md` | `/inferspec-scan` then `/inferspec-cap user-auth` | **Converged** — all `[GAP]` markers resolved via interactive Q&A; footer carries `last_qa_run` |
| `openspec/specs/order-management/spec.md` | `/inferspec-scan` only | Draft — contains `[GAP]` markers awaiting `/inferspec-cap` |
| `openspec/specs/health-check/spec.md` | `/inferspec-scan` only | Draft — contains `[GAP]` markers awaiting `/inferspec-cap` |

Compare `user-auth/spec.md` (no `[GAP]` markers, explicit "demo-only" Purpose,
strengthened SHALL clauses for anti-enumeration and token-placeholder intent)
against `order-management/spec.md` or `health-check/spec.md` to see what one
round of cap-mode Q&A buys you.

## Reproduce

```
# In your AI agent, with the inferspec uvx package installed:
cd examples/legacy-flask-app
/inferspec-scan                      # produces all three drafts
/inferspec-cap user-auth             # converges user-auth interactively
```
