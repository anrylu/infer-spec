# /inferspec-cap — Design (v0.2)

**Status:** Draft for v0.2
**Date:** 2026-05-20
**Author:** anrylu
**Parent:** `docs/superpowers/specs/2026-05-20-inferspec-design.md`
**Related v0.1 deliverable:** `/inferspec-scan` (bulk mode)

---

## 1. Positioning

`/inferspec-cap` is InferSpec's **single-capability deep-dive skill** with an
interactive Q&A loop. Where `/inferspec-scan` writes ambient drafts for every
capability in a repo, `/inferspec-cap` zooms in on one capability and converges
its spec by:

1. Proactively soliciting external context (Jira tickets, Confluence pages, URLs)
   that wouldn't be visible to a passive scan.
2. Reading the cap's source, git history, existing spec draft (if any), and the
   solicited context.
3. **Asking the user targeted questions about each `[GAP]` / `[TBD]` marker**,
   one at a time.
4. Rewriting the affected Requirement/Scenario in place after each answer.
5. Repeating until no markers remain or the user says "enough".

The dogfood on `examples/legacy-flask-app/` produced 16 `[GAP]` markers across 3
caps after `/inferspec-scan`. `/inferspec-cap` is the tool that turns those
markers into firm Requirements.

### Differentiation from `/inferspec-scan`

| Aspect | `/inferspec-scan` | `/inferspec-cap` |
|---|---|---|
| Scope | All caps in repo | One cap (by slug or by user description) |
| Interactivity | None — drafts even with gaps | Active per-gap Q&A loop |
| Context sources | Auto-detect what's available | Same + actively prompts user for tickets/URLs |
| Output stability | Drafts marked with `[GAP]` | Converged spec, ideally zero `[GAP]` |
| When to use | Onboarding a new repo | Locking down a critical capability |

---

## 2. Inputs and modes

### 2.1 Invocation

```
/inferspec-cap <slug>            # explicit slug from features.json
/inferspec-cap "user auth"       # fuzzy match; skill resolves to closest slug
/inferspec-cap                   # interactive picker (list known caps + "new")
/inferspec-cap <slug> --new      # force-bootstrap; ignore any existing draft
```

### 2.2 Resolution rules

1. If `graphify-out/features.json` doesn't exist, prompt user to run
   `/inferspec-scan` first (or offer to run it inline).
2. If slug is given and matches a cap in features.json exactly → use it.
3. If a fuzzy phrase is given → propose the top 3 nearest caps (slug + file list),
   let user pick.
4. If user requests a cap that's NOT in features.json (e.g. focusing on a new
   feature being added) → enter **bootstrap mode**: ask user to point to the
   relevant files, then add the cap to features.json.

---

## 3. The Q&A loop (core mechanism)

### 3.1 Loop structure

```
1. Gather context (Step 4 below).
2. Draft spec.md from scratch OR load existing draft.
3. Extract every [GAP] / [TBD] marker → ordered question queue.
4. For each marker:
     a. Show the user the surrounding Requirement + Scenario for context.
     b. Ask ONE focused question. Include candidate answers when sensible
        (multiple choice).
     c. Receive user reply.
     d. Rewrite the affected Requirement (not the entire spec) inline.
     e. Remove the marker. Re-validate: did the rewrite introduce new gaps?
        If yes, append them to the queue.
     f. Show a 2-line diff summary so user confirms before moving on.
5. After queue is empty (or user says "enough"):
     a. Update `__inferspec_meta__` footer with fresh hash + timestamp.
     b. Report unresolved markers (if any).
     c. Do NOT auto-commit.
```

### 3.2 Question quality rules

The skill must:

- **Ask the smallest question that resolves the marker.** "Is the rate limit
  5/60s or different?" beats "Tell me how the rate limiter works."
- **Offer candidate answers** when behaviour is binary or small-cardinality.
  Example: "Unknown-user returns 401 same as wrong-password. (a) intentional
  anti-enumeration (b) accidental — should return 404. Which?"
- **Cite file:line** where the ambiguity lives so the user can look it up.
- **Acknowledge "I don't know" gracefully**: if user can't answer, downgrade
  the `[GAP]` to `[TBD]` and move on. Don't pester.
- **Group related markers** when one answer resolves multiple. Example: if
  user says "auth is required everywhere", a single answer can clear gaps in
  multiple capabilities — the skill should detect this and propose batch
  resolution before iterating one-by-one.

### 3.3 Loop termination

Stop conditions:
- Queue empty.
- User types "stop", "enough", "done", or any quit-like phrase.
- All remaining markers are `[TBD]` (user already deferred them).

Never loop more than `N=50` iterations per skill invocation; if hit, ask user to
re-invoke (prevents runaway sessions).

---

## 4. Context gathering (extends /inferspec-scan)

`/inferspec-cap` collects everything `/inferspec-scan` collects, **plus**:

| Source | How it's gathered |
|---|---|
| Cap source files | Read tool (same as scan) |
| Git log + blame for cap files | `git log` + `git blame` (deeper than scan; cap mode reads the blame to point at specific commit messages per line when answering a [GAP]) |
| Local docs matching the cap | Glob + filename/content match (same as scan) |
| **Jira tickets** | If MCP available, the skill EXPLICITLY ASKS "any Jira ticket(s) for this cap?" rather than searching by slug only. User can paste 0..N ticket IDs. |
| **Confluence pages** | Same — explicit ask, accept URLs or page IDs. |
| **Arbitrary URLs** | The skill asks "any other docs, design pages, or PR threads I should read?" — uses host's WebFetch on whatever URLs the user pastes. |
| **Prior spec draft** | If `openspec/specs/<slug>/spec.md` exists, load it. The Q&A loop operates on its `[GAP]`/`[TBD]` markers directly. |

Token budget per cap: ~16K input (vs scan's 8K) because cap mode is willing to
spend more on one cap.

---

## 5. Output

### 5.1 File written

Same path and format as `/inferspec-scan`:
`openspec/specs/<slug>/spec.md` with `## Purpose` + `## Requirements` and the
`__inferspec_meta__` footer.

### 5.2 Footer changes

Append a `last_qa_run` field to the meta block so we can tell whether a spec
was last touched by scan or by cap mode:

```html
<!-- __inferspec_meta__: {"hash": "...", "scan_ts": "...", "last_qa_run": "2026-05-21T...", "version": "0.1"} -->
```

`last_qa_run` is absent on scan-produced files and present on cap-produced files.

### 5.3 Conversation transcript (optional artefact)

The Q&A loop can optionally save a transcript to
`openspec/specs/<slug>/_qa_log.md` (gitignored by default) so the user can
review which questions were asked and how they answered.

**Default: no transcript.** Enabled via `--save-transcript` flag.

---

## 6. New skill: `/inferspec-cap`

### 6.1 File layout

```
src/inferspec/skills/inferspec-cap/
├── SKILL.md
├── prompts/
│   ├── resolve_cap.md           # cap-slug resolution + bootstrap
│   ├── solicit_sources.md       # the "any tickets/URLs?" prompt
│   ├── ask_gap.md               # how to phrase a [GAP] question
│   ├── rewrite_requirement.md   # how to rewrite a Requirement from an answer
│   └── batch_detect.md          # find markers resolvable by one shared answer
└── (reuses spec_template.md from /inferspec-scan via relative path or copy)
```

### 6.2 Shared assets with /inferspec-scan

`spec_template.md` is shared — to avoid duplication, the v0.2 installer copies
`src/inferspec/skills/_shared/spec_template.md` into each skill bundle that
needs it. (Refactor target: pull spec_template out of `inferspec-scan/` into
`_shared/` before v0.2 ships.)

### 6.3 Installer change

The installer already iterates `src/inferspec/skills/*/` and copies each one,
so adding `inferspec-cap/` is automatic. No installer code change required.
Test coverage updates: `test_installed_skill_has_required_files` already asserts
about `inferspec-scan` only — add a `test_installed_skill_inferspec_cap_files`.

---

## 7. MVP (v0.2) scope

### 7.1 In scope

- `/inferspec-cap` skill with the Q&A loop described in §3
- Cap slug resolution (exact, fuzzy, interactive picker)
- Bootstrap mode for caps not yet in features.json
- Source solicitation: explicit Jira/Confluence/URL prompt
- `[GAP]` and `[TBD]` queue processing with per-Requirement rewrite
- Footer update with `last_qa_run`
- New unit test in installer test suite
- Shared `spec_template.md` extracted to `_shared/`
- README + multi-language READMEs updated with the new skill

### 7.2 Out of scope (v0.3+)

- `/inferspec-refine` (gap-only mode without bootstrap) — re-evaluate whether
  this is distinct enough from `/inferspec-cap` to justify a separate skill.
  If `/inferspec-cap` covers it cleanly via "load existing → resolve markers",
  `/inferspec-refine` may be cut entirely.
- Multi-cap parallel Q&A in one session
- Transcript logging by default
- Spec-vs-code drift detection
- Auto-commit on convergence

### 7.3 Success criteria

v0.2 ships when:

1. `/inferspec-cap user-auth` on the Flask demo resolves all 7 `[GAP]` markers
   in `user-auth/spec.md` to firm Requirements (or downgrades to `[TBD]`),
   without me hand-editing the markdown.
2. `/inferspec-cap "rate limit"` (fuzzy) correctly proposes `user-auth` as the
   match.
3. `/inferspec-cap new-feature --new` on a hypothetical cap (e.g., a new file
   added to the demo) produces a spec from scratch with the same format.
4. Footer `last_qa_run` is populated after a cap-mode run.
5. Installer copies `inferspec-cap/` into the host skill path.
6. Full test suite green.

---

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Q&A loops feel naggy if too many gaps | Group-detect (§3.2) and offer batch resolution; allow "skip", "TBD", "stop" at any iteration |
| User can't answer a gap — gets stuck | Downgrade `[GAP]` to `[TBD]` and move on; never block |
| Rewrite introduces new gaps in cascading manner | Re-validate after each rewrite; cap queue at 50 |
| Conflict with existing draft if user has hand-edited spec.md | Detect hash mismatch in footer; ask user before overwriting hand edits |
| Shared `spec_template.md` refactor breaks `/inferspec-scan` | The refactor is one task in the v0.2 plan; test_installed_skill_has_required_files updated to expect the new path |

---

## 9. Resolved decisions

- **Q1 — Write target: direct to `spec.md`.** No `.next` / `.bak` staging.
  Single source of truth. Per-answer preview is the 2-line diff summary shown
  in step 4f of the loop; the escape hatch is `git checkout -- spec.md`.
- **Q2 — Batch resolve: single explicit prompt, LLM-driven conservative
  grouping.** When the skill detects that several `[GAP]` markers share a
  semantic theme (e.g., "auth requirement" across multiple Requirements), it
  proposes a batch: lists every marker it would include and asks the user
  to confirm before answering once. If the user declines, fall back to
  per-marker iteration. Grouping logic is LLM judgement, not pattern matching —
  the skill prefers to MISS a batch than to wrongly bundle unrelated gaps.
- **Q3 — End-of-session commit prompt.** When the loop exits (queue empty or
  user-stopped), ask once: "Commit these spec changes? (y/n)". On yes, run
  `git add openspec/specs/<slug>/spec.md && git commit -m "spec: refine <slug>
  via /inferspec-cap"`. On no, leave the working tree dirty for the user.
  Commit message template is fixed; users wanting a custom message answer "no"
  and commit manually.
