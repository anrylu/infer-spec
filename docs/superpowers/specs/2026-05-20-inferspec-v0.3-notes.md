# InferSpec v0.3 — Design Notes

**Status:** Draft (post-v0.2 dogfood)
**Date:** 2026-05-20
**Parent:** `docs/superpowers/specs/2026-05-20-inferspec-cap-design.md`

This document captures UX findings from the v0.2 dogfood of `/inferspec-cap`
on `examples/legacy-flask-app/` (cap = `user-auth`, 7 markers resolved in one
session, 0 deferred). Each finding is logged with a concrete v0.3 proposal so
it can be turned into an implementation plan.

---

## Findings

### F1 — Source solicitation is too verbose when context is obviously empty

**Observed:** Step 2 of `/inferspec-cap` is implemented as 4 separate single-
question prompts (Jira ticket / Confluence page / URL / freeform). For demo
projects, internal tools, or any cap where the user clearly has no external
artefacts, this round of asking burns 4 turns to produce 4 "skip" answers.

**Mitigated already in v0.2:** Jira/Confluence questions are skipped when the
respective MCP server is absent. That's correct but only covers the obvious
case.

**v0.3 proposal:** When both Jira and Confluence MCPs are absent, consolidate
the URL + freeform questions into a single prompt:

> "Any external context to add for `<cap>`? Paste URL(s), notes, or 'skip'."

Detect URLs in the answer (any `https?://...` match) → WebFetch each; the
remainder is treated as freeform text. This collapses Step 2 from 2 turns
(URL + freeform) to 1 turn in the common case, with no loss of capability.

If either Jira or Confluence MCP is present, keep the per-source prompts —
those need distinct parsing logic (ticket IDs vs URLs).

**File:** `src/inferspec/skills/inferspec-cap/prompts/solicit_sources.md`

---

### F2 — Numeric answers (`1` / `2` / `3` ...) should be equivalent to letter answers (`a` / `b` / `c` ...)

**Observed:** During dogfood, the user answered marker M3 with `1` instead of
`a`. The current `ask_gap.md` prompt template only shows letter options
(`(a)`, `(b)`, `(c)`...) and doesn't tell the LLM to accept numeric variants.
The LLM correctly inferred "1 = (a)" but that inference is fragile.

**v0.3 proposal:** Update `ask_gap.md` to explicitly state:

> Accept the user's answer as `(a)` / `(b)` / `(c)` / `(d)` / ... OR as
> `1` / `2` / `3` / `4` / ... — both forms map to the same option by
> position. Also accept the full option text quoted back.

**File:** `src/inferspec/skills/inferspec-cap/prompts/ask_gap.md`

---

### F3 — Cap-mode rewrites are stronger than "fill the blank"

**Observed:** 5 of 7 marker resolutions in the dogfood triggered real
Requirement strengthening, not just `[GAP]` comment removal:

| Marker | Edit type |
|---|---|
| M1 (Purpose) | Rewrote entire Purpose paragraph with explicit "demo-only / no production threat model" framing |
| M2 (token format) | Added new SHALL clause to Requirement: "production deployment MUST replace" |
| M3 (missing JSON) | Strengthened THEN line with explicit rationale |
| M4 (anti-enumeration) | Added explicit SHALL indistinguishability clause; updated both scenarios with AND lines |
| M6+M7 (rate-limit state) | Added new Scenario for restart behaviour; renamed user-store scenario for clarity |

**This is the right behaviour** — confirming intent often demands structural
changes, not cosmetic ones. The current `rewrite_requirement.md` already
allows this (rule 4 covers new scenarios, rule 5 covers keyword changes).

**No proposal — this is a positive finding.** Document it in marketing copy
or the README as a value-add over scan-only mode.

---

### F4 — Batch detect is conservative-enough

**Observed:** The dogfood had one obvious batch candidate (M6+M7, both about
rate-limit state lifecycle) and one near-miss (M1+M2, both about token
scheme but M1 also asked about threat model). The skill correctly proposed
M6+M7 as a batch and did NOT propose M1+M2 — the latter was correctly
asked individually because M1 had additional scope.

**No proposal — this is a positive finding.** The conservative grouping rule
("when in doubt, don't batch") is working as designed.

---

### F5 — Per-marker iteration cost is OK for ≤10 markers; will not scale to dozens

**Observed:** The dogfood took 6 question prompts to resolve 7 markers (1
batch covering 2 + 5 individual). Total session was roughly 10 minutes
elapsed and felt productive.

**Concern:** A real legacy capability could easily produce 20–50 `[GAP]`
markers from one scan. At that scale, 20+ sequential prompts is fatiguing.

**v0.3 proposal:** Add a `--review` mode that:

1. Renders ALL pending markers as a single summary view (marker text +
   surrounding Requirement + a suggested answer based on code/context).
2. Lets the user accept-all / accept-some / drop-into-individual-mode for
   the rest.
3. Falls back to per-marker mode for any marker the user didn't accept.

Invocation:
```
/inferspec-cap <slug> --review
```

This is opt-in — default behaviour stays the same so users with a few markers
don't pay for the larger context.

**File:** New mode in `src/inferspec/skills/inferspec-cap/SKILL.md` Step 5,
plus a new prompt `src/inferspec/skills/inferspec-cap/prompts/review_mode.md`.

---

## Proposed v0.3 scope

In order of estimated value-per-effort:

1. **F2 (numeric answers)** — one-line addition to `ask_gap.md`. Low cost,
   small but real UX win.
2. **F1 (consolidate solicit_sources for MCP-less environments)** — one
   prompt edit + slight orchestration change in SKILL.md. Cuts 1 turn from
   the common case.
3. **F5 (`--review` mode)** — biggest change; new prompt + new SKILL.md
   branch + tests. Only worth doing if dogfood reveals scaling pain on a
   real cap (>15 markers).

F3 and F4 require no code; they become README copy or design-doc citations.

## Decision on `/inferspec-refine`

The v0.1 design committed to shipping `/inferspec-refine` as a separate skill
in v0.3. The dogfood confirms what the v0.2 design hypothesised: `/inferspec-cap`
in "existing spec" mode already handles refine semantics cleanly — load
existing draft, iterate markers, commit. **Recommendation: cut `/inferspec-refine`
as a separate skill.** Document `/inferspec-cap` as the gap-fill tool too.

## v0.3 not in scope

- PyPI release (still post-v0.3 to keep release noise bundled)
- Multi-cap parallel Q&A
- Auto-commit beyond the single end-of-session prompt
- Spec-vs-code drift detection
