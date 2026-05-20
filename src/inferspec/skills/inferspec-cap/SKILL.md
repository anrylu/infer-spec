---
name: inferspec-cap
description: Deep-dive single-capability OpenSpec drafter with interactive Q&A to resolve [GAP]/[TBD] markers. Triggered by /inferspec-cap.
---

# /inferspec-cap

Take ONE capability deep — solicit Jira/Confluence/URL context the user has,
draft (or reload) its OpenSpec `spec.md`, then ask the user one focused
question per `[GAP]` marker until the spec is converged.

`/inferspec-scan` writes ambient drafts for the whole repo. `/inferspec-cap` is
how you turn one draft (or no draft) into a firm spec.

## Output

Writes / overwrites `openspec/specs/<slug>/spec.md` in OpenSpec format. Adds
`last_qa_run` field to the `__inferspec_meta__` footer. On exit (with user's
consent), commits the change.

## Usage

```
/inferspec-cap <slug>              # explicit slug from features.json
/inferspec-cap "user auth"         # fuzzy match
/inferspec-cap                     # interactive picker
/inferspec-cap <slug> --new        # bootstrap a new cap
/inferspec-cap <slug> --save-transcript   # save Q&A log
```

## When this skill is invoked, run these steps

### Step 0 — Parse flags + load context

Parse:
- `--new` → bootstrap mode
- `--save-transcript` → write `openspec/specs/<slug>/_qa_log.md` (gitignored)

Read `.inferspec.yaml` for any `mcp_overrides`.

### Step 1 — Resolve the cap

Read `prompts/resolve_cap.md` and follow it. Get a resolved `cap = {name, files,
existing_spec, existing_markers}`.

If `features.json` is missing, offer to run `/inferspec-scan` first. If user
agrees, invoke it then restart this step.

### Step 2 — Solicit external sources

Read `prompts/solicit_sources.md` and follow it. Gather
`cap.external_context = {jira, confluence, urls, freeform}`.

This step is what `/inferspec-scan` does NOT do — it actively asks. Don't
skip even if the user starts impatient; one prompt round is fast.

### Step 3 — Draft or reload spec

If `cap.existing_spec`:
- Read the existing `openspec/specs/<cap.name>/spec.md`.
- Extract all `[GAP]` and `[TBD]` markers (file, line, surrounding Requirement).
  Initialize `question_queue` with them.

Else:
- Follow `prompts/draft_spec.md` (from the `inferspec-scan` skill — same
  conventions) to draft a fresh spec using `cap.files` + git log +
  `cap.external_context`.
- Extract markers from the fresh draft into `question_queue`.

Write the spec (fresh or reloaded) to `openspec/specs/<cap.name>/spec.md`.

### Step 4 — Batch detect (once, up front)

Read `prompts/batch_detect.md` and follow it. Get zero or more candidate
groups.

For each group:
- Ask the user: "I see N markers all about <theme>. Answer once? (y/n)"
- If yes: ask the proposed question; on answer, rewrite every member
  Requirement in one pass.
- If no: leave those markers in the per-marker queue.

### Step 5 — Per-marker Q&A loop

While `question_queue` is non-empty AND user hasn't said "stop":

1. Pop the next marker.
2. Read `prompts/ask_gap.md` and ask the question.
3. Receive answer:
   - "stop" / "enough" → break out of the loop.
   - "tbd" / "I don't know" → downgrade marker `[GAP]` to `[TBD]` in spec.md;
     continue to next marker.
   - Concrete answer → continue to step 4.
4. Read `prompts/rewrite_requirement.md` and rewrite the affected
   Requirement block in `spec.md` in place.
5. Show user a 2-line diff summary of the change. Continue without waiting
   for confirmation (the user can `git diff` or `git checkout --` if they
   need to rollback).
6. Re-scan the rewritten Requirement for newly-introduced markers; append
   any to the queue.

Safety cap: max 50 iterations per skill invocation. If hit, report and exit.

### Step 6 — Footer update

After loop exit, update the `__inferspec_meta__` footer in spec.md:

```html
<!-- __inferspec_meta__: {"hash": "<fresh sha256>", "scan_ts": "<original or current>", "last_qa_run": "<current ISO-8601 UTC>", "version": "0.1"} -->
```

`hash` = recompute over the cap's source files (same as scan's hash).
`scan_ts` = preserve the original scan timestamp if present, else set to now.
`last_qa_run` = current UTC timestamp.

### Step 7 — End-of-session commit prompt

Report to the user:
```
Resolved: <N> markers
Deferred ([TBD]): <M>
Remaining ([GAP]): <K>
```

Then ask once:
```
Commit these spec changes? (y/n)
```

On `y`:
```bash
git add openspec/specs/<cap.name>/spec.md
git commit -m "spec: refine <cap.name> via /inferspec-cap"
```

On `n` or anything else: leave the working tree dirty.

### Step 8 — Optional transcript

If `--save-transcript` was set, write `openspec/specs/<cap.name>/_qa_log.md`
with each (marker, question, answer, rewrite-diff) entry. Ensure `_qa_log.md`
is gitignored — add to repo `.gitignore` if not already there:

```bash
if [ -f .gitignore ] && ! grep -qxF "**/_qa_log.md" .gitignore; then
    echo "**/_qa_log.md" >> .gitignore
fi
```

## Notes for the host AI

- This skill never calls a cloud LLM API. You ARE the LLM — execute the
  prompts inline.
- Direct write to `spec.md` is intentional (single source of truth). Use
  `git checkout -- spec.md` if a rewrite went wrong.
- The end-of-session commit prompt is the ONE place this skill is allowed
  to commit on behalf of the user.
- Per-marker re-validation in Step 5.6 is critical — rewrites can introduce
  new gaps, and the queue must keep up.
