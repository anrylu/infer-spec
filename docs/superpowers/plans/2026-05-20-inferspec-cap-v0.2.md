# InferSpec v0.2 — `/inferspec-cap` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `/inferspec-cap` — a single-capability deep-dive skill with an
interactive Q&A loop that converges `[GAP]`/`[TBD]` markers into firm
Requirements, with conservative batch resolution and an end-of-session commit
prompt.

**Architecture:** Pure markdown skill addition. The Python package, installer,
CLI, and platform registry are unchanged from v0.1. The installer already
iterates `src/inferspec/skills/*/`, so adding `inferspec-cap/` is automatic.
Reuse `managed_block` / `installer` / `platforms` unchanged.

**Tech Stack:** Markdown (skill prompts), pytest, click — no new Python deps.

**Spec reference:** `docs/superpowers/specs/2026-05-20-inferspec-cap-design.md`
(open questions Q1-Q3 already resolved in §9: direct write, single-prompt
conservative batch, end-of-session commit prompt).

**Scope cut:** This plan covers only `/inferspec-cap`. `/inferspec-refine` is
deferred to v0.3 pending evaluation of whether it's distinct from `/inferspec-cap`
in load-existing-spec mode. PyPI release stays out of scope.

---

## File Structure

```
infer-spec/
├── src/inferspec/
│   ├── skills/
│   │   ├── inferspec-scan/         # unchanged from v0.1
│   │   └── inferspec-cap/          # NEW
│   │       ├── SKILL.md
│   │       ├── spec_template.md    # copy from inferspec-scan/
│   │       └── prompts/
│   │           ├── resolve_cap.md
│   │           ├── solicit_sources.md
│   │           ├── ask_gap.md
│   │           ├── rewrite_requirement.md
│   │           └── batch_detect.md
│   └── installer.py                # UNCHANGED (already copies all skills/*/)
├── tests/
│   └── test_installer.py           # MODIFY — add inferspec-cap files test
├── README.md                       # MODIFY — mention /inferspec-cap
├── README.zh-tw.md                 # MODIFY
├── README.zh-cn.md                 # MODIFY
└── README.ja.md                    # MODIFY
```

**Responsibility split:**
- `SKILL.md` — the orchestration script (cap resolution → source solicitation → loop)
- `resolve_cap.md` — fuzzy match logic and `--new` bootstrap
- `solicit_sources.md` — the "any Jira ticket / Confluence / URL?" prompt
- `ask_gap.md` — how to phrase ONE focused question per `[GAP]`
- `rewrite_requirement.md` — how to rewrite a Requirement block from an answer
- `batch_detect.md` — conservative LLM-judgement grouping rules
- `spec_template.md` — copied from `inferspec-scan/` (duplication accepted for v0.2;
  `_shared/` extraction deferred until a third skill needs it)

---

## Task 1: Bootstrap `inferspec-cap` skill directory with stub SKILL.md

**Files:**
- Create: `src/inferspec/skills/inferspec-cap/SKILL.md` (stub for now; full
  content in Task 7)
- Create: `src/inferspec/skills/inferspec-cap/spec_template.md` (verbatim copy
  of `inferspec-scan/spec_template.md`)
- Create: `src/inferspec/skills/inferspec-cap/prompts/.gitkeep`

- [ ] **Step 1: Write stub SKILL.md**

`src/inferspec/skills/inferspec-cap/SKILL.md`:
```markdown
---
name: inferspec-cap
description: Deep-dive single-capability OpenSpec drafter with interactive Q&A to resolve [GAP]/[TBD] markers. Triggered by /inferspec-cap.
---

# /inferspec-cap

Placeholder — full skill content lands in Task 7.
```

- [ ] **Step 2: Copy spec_template.md**

```bash
cp src/inferspec/skills/inferspec-scan/spec_template.md \
   src/inferspec/skills/inferspec-cap/spec_template.md
```

- [ ] **Step 3: Create empty prompts dir marker**

```bash
mkdir -p src/inferspec/skills/inferspec-cap/prompts
touch src/inferspec/skills/inferspec-cap/prompts/.gitkeep
```

- [ ] **Step 4: Verify installer picks up the new skill**

Run:
```bash
PYTHONPATH=src .venv/bin/python -c "
from inferspec.installer import _bundled_skills_dir
from pathlib import Path
print(sorted(p.name for p in _bundled_skills_dir().iterdir() if p.is_dir()))
"
```
Expected: `['inferspec-cap', 'inferspec-scan']`

- [ ] **Step 5: Commit**

```bash
git add src/inferspec/skills/inferspec-cap/
git -c user.email=anrylu@qnap.com -c user.name=anrylu commit -m "feat: bootstrap inferspec-cap skill directory with stub SKILL.md"
```

---

## Task 2: `resolve_cap.md` — cap slug resolution + `--new` bootstrap

**Files:**
- Create: `src/inferspec/skills/inferspec-cap/prompts/resolve_cap.md`

- [ ] **Step 1: Write the prompt**

`src/inferspec/skills/inferspec-cap/prompts/resolve_cap.md`:
```markdown
You are resolving the user's `/inferspec-cap` argument to a concrete capability.

INPUT:
- `argv` — the raw argument(s) passed to /inferspec-cap. May be:
  - empty (no arg)
  - a slug like `user-auth`
  - a fuzzy phrase like "user auth", "rate limiting", "the login thing"
  - a slug followed by `--new` (force-bootstrap)
- `graphify-out/features.json` — list of known capabilities (may not exist)
- `openspec/specs/` directory (may not exist)

RESOLUTION RULES (apply in order, stop at first match):

1. **No features.json**: tell the user `/inferspec-scan` should run first.
   Offer to run it inline; if user agrees, run scan THEN restart cap resolution.

2. **Empty argv**: list every cap in features.json with its file count, plus a
   "(new)" option. Let user pick one. Resolved → cap.

3. **`--new` flag present**: bootstrap mode. Treat the slug before `--new` as
   the new cap's name; ask user for the relevant file paths (relative to repo
   root). Add the new cap to features.json. Resolved → new cap.

4. **Exact slug match in features.json**: resolved.

5. **Fuzzy phrase**: compute simple similarity (split phrase on whitespace,
   look for any token appearing in a slug or its file paths). Rank top 3.
   Show the user with file counts and ask them to pick. Resolved → chosen cap.

6. **No match at all**: tell the user and offer the empty-argv flow.

OUTPUT: a single resolved cap object `{name, files}`. Pass it to the next step
(source solicitation).

If the cap already has an `openspec/specs/<name>/spec.md`, also record:
- `existing_spec: true`
- `existing_markers: [<list of (file, line, marker text)>]`

These flow into the Q&A loop's initial queue.
```

- [ ] **Step 2: Commit**

```bash
git add src/inferspec/skills/inferspec-cap/prompts/resolve_cap.md
git -c user.email=anrylu@qnap.com -c user.name=anrylu commit -m "feat(cap): cap slug resolution prompt with fuzzy + bootstrap"
```

---

## Task 3: `solicit_sources.md` — proactive Jira/Confluence/URL prompt

**Files:**
- Create: `src/inferspec/skills/inferspec-cap/prompts/solicit_sources.md`

- [ ] **Step 1: Write the prompt**

`src/inferspec/skills/inferspec-cap/prompts/solicit_sources.md`:
```markdown
You are gathering external context for the resolved capability BEFORE drafting.

This step is what distinguishes /inferspec-cap from /inferspec-scan. Scan is
passive; cap actively asks the user.

INPUT:
- `cap` — resolved `{name, files}` from Step 1
- Available host tools — check whether `mcp__*__jira_*`, `mcp__*__confluence_*`,
  and a WebFetch-like tool are present.

ASK SEQUENCE (one prompt at a time; user may answer "skip" to any):

1. **Jira tickets** (only if Jira MCP available):
   "Any Jira ticket(s) for `<cap.name>`? Paste IDs (e.g. `AUTH-456, AUTH-789`) or 'skip'."
   - Parse IDs from reply; fetch each via the Jira MCP. Collect title + description + recent comments.

2. **Confluence pages** (only if Confluence MCP available):
   "Any Confluence page(s) for `<cap.name>`? Paste URLs or page IDs, or 'skip'."
   - Fetch each via the Confluence MCP. Collect page body.

3. **Arbitrary URLs** (always — relies on host's WebFetch):
   "Any other docs to consult (PR threads, design pages, RFCs)? Paste URL(s) or 'skip'."
   - For each URL, use the host's WebFetch tool. Collect rendered body text.

4. **Hand-pasted text** (always):
   "Anything else I should know about `<cap.name>`? Paste text or 'skip'."

Collect everything into a `cap.external_context` dict:
```json
{
  "jira": [{"id": "AUTH-456", "title": "...", "body": "..."}],
  "confluence": [{"url": "...", "title": "...", "body": "..."}],
  "urls": [{"url": "...", "body": "..."}],
  "freeform": "...user-pasted text..."
}
```

Token budget: cap entire `external_context` at ~8K tokens. Summarise lengthy
Jira/Confluence bodies; keep titles, acceptance criteria, and any explicit
numbers (limits, timeouts, etc.) verbatim.

Pass `cap.external_context` to drafting and to the Q&A loop.
```

- [ ] **Step 2: Commit**

```bash
git add src/inferspec/skills/inferspec-cap/prompts/solicit_sources.md
git -c user.email=anrylu@qnap.com -c user.name=anrylu commit -m "feat(cap): source solicitation prompt for Jira/Confluence/URLs"
```

---

## Task 4: `ask_gap.md` — how to phrase a single `[GAP]` question

**Files:**
- Create: `src/inferspec/skills/inferspec-cap/prompts/ask_gap.md`

- [ ] **Step 1: Write the prompt**

`src/inferspec/skills/inferspec-cap/prompts/ask_gap.md`:
```markdown
You are asking the user ONE focused question about a `[GAP]` (or `[TBD]`)
marker in the cap's spec.

INPUT:
- `marker` — `{file, line, text, surrounding_requirement, surrounding_scenario}`
- `cap.external_context` — Jira/Confluence/URL content gathered earlier

ASK RULES (mandatory):

1. **Smallest possible question.** Don't say "Tell me about the rate limiter."
   Say "Is the rate limit 5 failures / 60 seconds (as inferred from
   `auth.py:9-15`) or different?"

2. **Offer candidate answers when possible.** Prefer multiple choice for
   binary or small-cardinality decisions:
   > "Unknown-user returns 401 same as wrong-password. Pick:
   > (a) intentional — anti-user-enumeration
   > (b) accidental — should be 404
   > (c) other — explain"

3. **Cite file:line for the source of the ambiguity.** Always.

4. **One question per iteration.** Don't ask compound questions like "Is the
   limit X AND should the counter reset on success?". Split.

5. **Re-state the marker text verbatim in a quote block** before asking — so
   the user knows exactly which marker is being addressed.

ACCEPT RESPONSES:

- A concrete answer → pass to `rewrite_requirement.md`.
- "TBD" / "I don't know" / "skip" → downgrade marker from `[GAP]` to `[TBD]`
  in-place; do not rewrite the Requirement; move to next marker.
- "stop" / "enough" / "done" → exit the loop with whatever's still unresolved.
- Anything else → ask for clarification once; if still ambiguous, treat as TBD.

OUTPUT for downstream rewrite step:
```json
{
  "marker_id": "...",
  "user_answer": "...",
  "decision": "answered" | "tbd" | "stop"
}
```
```

- [ ] **Step 2: Commit**

```bash
git add src/inferspec/skills/inferspec-cap/prompts/ask_gap.md
git -c user.email=anrylu@qnap.com -c user.name=anrylu commit -m "feat(cap): question-phrasing prompt for individual [GAP] markers"
```

---

## Task 5: `rewrite_requirement.md` — rewrite a Requirement from an answer

**Files:**
- Create: `src/inferspec/skills/inferspec-cap/prompts/rewrite_requirement.md`

- [ ] **Step 1: Write the prompt**

`src/inferspec/skills/inferspec-cap/prompts/rewrite_requirement.md`:
```markdown
You are rewriting ONE Requirement block in `openspec/specs/<cap>/spec.md`
based on the user's answer to a `[GAP]` question.

INPUT:
- `requirement_block` — the existing `### Requirement: ...` block, verbatim
- `marker` — the `[GAP]` text being resolved
- `user_answer` — the answer text from the user
- `spec_full_text` — the entire current spec (for cross-reference, do not
  rewrite anything else)

REWRITE RULES:

1. **Touch only this Requirement block.** Don't edit Purpose, sibling
   Requirements, or the meta footer.

2. **Remove the resolved marker.** Replace `<!-- [GAP: ...] -->` with nothing
   (delete the HTML comment) once the Scenario/THEN line reflects the answer.

3. **Preserve `**Source:**` citations.** Add new citations if the user
   referenced new file:line ranges or ticket IDs.

4. **If the answer reveals a new edge case**, add a new `#### Scenario:` for
   it — but only inside this Requirement. New cross-Requirement scenarios
   should surface as a new `[GAP]` instead (will be added to the queue).

5. **If the answer changes the RFC 2119 keyword** (e.g., user says "actually
   that's optional, not required"), update SHALL → MAY or vice versa.

6. **Follow draft_spec.md conventions** for Scenarios — same AND/BUT rules,
   same one-claim-per-scenario rule.

OUTPUT: the rewritten Requirement block as a full string, ready to splice
back into spec.md replacing the original block.

After splicing, the orchestrator (SKILL.md) will:
- Re-scan the modified spec for `[GAP]` markers.
- Append any NEW markers introduced by the rewrite to the question queue.
- Show the user a 2-line diff summary of what changed.
- Move to the next marker.
```

- [ ] **Step 2: Commit**

```bash
git add src/inferspec/skills/inferspec-cap/prompts/rewrite_requirement.md
git -c user.email=anrylu@qnap.com -c user.name=anrylu commit -m "feat(cap): Requirement rewrite prompt"
```

---

## Task 6: `batch_detect.md` — conservative LLM-judgement grouping

**Files:**
- Create: `src/inferspec/skills/inferspec-cap/prompts/batch_detect.md`

- [ ] **Step 1: Write the prompt**

`src/inferspec/skills/inferspec-cap/prompts/batch_detect.md`:
```markdown
You are deciding whether several `[GAP]` markers can be resolved by ONE user
answer ("batch resolve").

INPUT:
- `markers` — list of unresolved markers in the current cap's spec

JUDGEMENT RULES:

1. **Group only by SEMANTIC THEME, not by location.** Two markers in the same
   file aren't necessarily a batch; two markers asking about "auth" across
   different Requirements MAY be.

2. **Conservative bias.** When in doubt, do NOT batch. The cost of a wrongly
   bundled batch (user answers once, wrong scope of changes) is higher than
   the cost of asking a few extra questions.

3. **Minimum group size: 2.** Don't propose a "batch" of one marker.

4. **Maximum group size: 5.** Above 5, the user is overwhelmed; split.

5. **Each candidate group must pass this test**: "If the user answered the
   single question that captures this group's theme, would all members of the
   group be resolved by the same rewrite logic?" If the answer is anything
   other than a clear yes — don't batch.

OUTPUT: zero or more candidate groups, each:
```json
{
  "theme": "auth requirement on order endpoints",
  "markers": ["marker_id_1", "marker_id_3", "marker_id_5"],
  "proposed_question": "Are /orders endpoints meant to require auth? (y/n)"
}
```

The orchestrator presents each group to the user as a single prompt:

> "I see 3 markers all about whether /orders requires auth (in
>  user-auth/spec.md:67, order-management/spec.md:14, order-management/spec.md:78).
>  Answer once for all three? (y/n)"

If user says yes → answer-once flow.
If user says no → fall back to per-marker iteration.
```

- [ ] **Step 2: Commit**

```bash
git add src/inferspec/skills/inferspec-cap/prompts/batch_detect.md
git -c user.email=anrylu@qnap.com -c user.name=anrylu commit -m "feat(cap): batch-resolve detection prompt with conservative grouping"
```

---

## Task 7: Full SKILL.md (the orchestration script)

**Files:**
- Modify: `src/inferspec/skills/inferspec-cap/SKILL.md` — replace stub

- [ ] **Step 1: Replace stub with full content**

`src/inferspec/skills/inferspec-cap/SKILL.md`:
```markdown
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
```

- [ ] **Step 2: Reinstall global skill to pick up changes**

Run:
```bash
cd ~ && /Users/anrylu/Documents/workspace/infer-spec/.venv/bin/inferspec init --platform claude-code 2>&1 | tail -3
cd /Users/anrylu/Documents/workspace/infer-spec
```
Expected: `Done. Open your AI agent...`

- [ ] **Step 3: Verify SKILL.md frontmatter**

Run:
```bash
.venv/bin/python -c "
from pathlib import Path
import re
p = Path('src/inferspec/skills/inferspec-cap/SKILL.md').read_text()
assert p.startswith('---'), 'frontmatter missing'
assert re.search(r'^name:\s*inferspec-cap', p, re.M), 'bad name'
m = re.search(r'^description:\s*(.+)$', p, re.M)
assert m and len(m.group(1).strip()) > 20, 'description too short'
print('SKILL.md frontmatter OK')
"
```
Expected: `SKILL.md frontmatter OK`

- [ ] **Step 4: Commit**

```bash
git add src/inferspec/skills/inferspec-cap/SKILL.md
git -c user.email=anrylu@qnap.com -c user.name=anrylu commit -m "feat(cap): full SKILL.md with Q&A loop, batch detect, end-of-session commit prompt"
```

---

## Task 8: Installer test coverage for inferspec-cap

**Files:**
- Modify: `tests/test_installer.py` — add `test_installed_cap_skill_has_required_files`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_installer.py`:
```python
def test_installed_cap_skill_has_required_files(tmp_path: Path):
    p = get_platform("claude-code")
    install_platform(tmp_path, p)
    skill_root = tmp_path / p.skills_path / "inferspec-cap"

    # Top-level files
    assert (skill_root / "SKILL.md").exists()
    assert (skill_root / "spec_template.md").exists()

    # All 5 prompt files
    prompts_dir = skill_root / "prompts"
    for name in (
        "resolve_cap.md",
        "solicit_sources.md",
        "ask_gap.md",
        "rewrite_requirement.md",
        "batch_detect.md",
    ):
        assert (prompts_dir / name).exists(), f"missing {name}"

    skill_text = (skill_root / "SKILL.md").read_text()
    assert "name: inferspec-cap" in skill_text
    assert "[GAP]" in skill_text
    assert "commit" in skill_text.lower()
```

- [ ] **Step 2: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_installer.py -v`
Expected: 6 passed (5 existing + 1 new).

Also run full suite: `.venv/bin/pytest -v`
Expected: 23 passed (22 existing + 1 new).

- [ ] **Step 3: Commit**

```bash
git add tests/test_installer.py
git -c user.email=anrylu@qnap.com -c user.name=anrylu commit -m "test: installer copies inferspec-cap skill bundle"
```

---

## Task 9: E2E install test against Flask demo (extend existing)

**Files:**
- Modify: `tests/test_e2e_install.py` — extend assertions

- [ ] **Step 1: Update existing test**

Modify `tests/test_e2e_install.py` — locate `test_install_into_flask_demo` and
update its assertions to also cover the new skill. Replace the existing
assertion block with:

```python
def test_install_into_flask_demo(flask_demo_copy: Path):
    p = get_platform("claude-code")
    install_platform(flask_demo_copy, p)

    # inferspec-scan
    scan_root = flask_demo_copy / p.skills_path / "inferspec-scan"
    assert (scan_root / "SKILL.md").exists()
    assert (scan_root / "spec_template.md").exists()
    assert (scan_root / "prompts" / "classify_capabilities.md").exists()
    assert (scan_root / "prompts" / "draft_spec.md").exists()

    # inferspec-cap (NEW)
    cap_root = flask_demo_copy / p.skills_path / "inferspec-cap"
    assert (cap_root / "SKILL.md").exists()
    assert (cap_root / "spec_template.md").exists()
    for prompt_name in (
        "resolve_cap.md",
        "solicit_sources.md",
        "ask_gap.md",
        "rewrite_requirement.md",
        "batch_detect.md",
    ):
        assert (cap_root / "prompts" / prompt_name).exists()

    # Managed block in config
    config = flask_demo_copy / p.config_file
    assert config.exists()
```

Leave `test_skill_references_existing_prompt_files` unchanged (it asserts the
scan SKILL.md references its own prompt files, which is still correct).

- [ ] **Step 2: Run tests**

Run: `.venv/bin/pytest tests/test_e2e_install.py -v`
Expected: 2 passed.

Full suite: `.venv/bin/pytest -v`
Expected: 23 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e_install.py
git -c user.email=anrylu@qnap.com -c user.name=anrylu commit -m "test: e2e install now covers both inferspec-scan and inferspec-cap"
```

---

## Task 10: Update managed block content + CLI doctor to reference both skills

**Files:**
- Modify: `src/inferspec/installer.py` — update `_managed_block_content()`
- Modify: `src/inferspec/cli.py` — update `doctor` to check both skill dirs

- [ ] **Step 1: Update managed block content**

In `src/inferspec/installer.py`, replace `_managed_block_content()` with:

```python
def _managed_block_content() -> str:
    return (
        "# InferSpec\n"
        "\n"
        "This repo has InferSpec skills installed. Available slash commands:\n"
        "\n"
        "- `/inferspec-scan` — bulk-infer OpenSpec specs from code + git + docs\n"
        "- `/inferspec-cap <slug>` — single-cap deep-dive with interactive Q&A\n"
        "\n"
        "Specs are written to `openspec/specs/<cap>/spec.md`.\n"
        "See https://github.com/anrylu/infer-spec for docs.\n"
    )
```

- [ ] **Step 2: Update doctor command**

In `src/inferspec/cli.py`, modify the `doctor` command body. Replace this
block:

```python
        skill = project_dir / p.skills_path / "inferspec-scan" / "SKILL.md"
        config = project_dir / p.config_file
        skill_ok = skill.exists()
        block_ok = config.exists() and START_MARKER in config.read_text()
        mark = "[green]✓[/green]" if skill_ok and block_ok else "[red]✗[/red]"
        console.print(f"  {mark} {p.name} ({p.id}): skill={skill_ok} block={block_ok}")
```

with:

```python
        scan_skill = project_dir / p.skills_path / "inferspec-scan" / "SKILL.md"
        cap_skill = project_dir / p.skills_path / "inferspec-cap" / "SKILL.md"
        config = project_dir / p.config_file
        scan_ok = scan_skill.exists()
        cap_ok = cap_skill.exists()
        block_ok = config.exists() and START_MARKER in config.read_text()
        all_ok = scan_ok and cap_ok and block_ok
        mark = "[green]✓[/green]" if all_ok else "[red]✗[/red]"
        console.print(
            f"  {mark} {p.name} ({p.id}): scan={scan_ok} cap={cap_ok} block={block_ok}"
        )
```

The exact source-line bounds of the doctor command may have shifted since v0.1
— locate the original block by text content, not line numbers.

- [ ] **Step 3: Update uninstall to also remove cap skill dir**

Locate the uninstall command body, find this block:

```python
        skill_dir = project_dir / p.skills_path / "inferspec-scan"
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
```

Replace with:

```python
        for skill_name in ("inferspec-scan", "inferspec-cap"):
            skill_dir = project_dir / p.skills_path / skill_name
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
```

- [ ] **Step 4: Update CLI tests to expect the new doctor output format**

In `tests/test_cli.py`, `test_doctor_reports_status` currently asserts
`"claude-code" in result.output.lower()`. That still holds. But also add
assertions for the new format:

Find the existing test:
```python
def test_doctor_reports_status(tmp_path: Path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init", "--platform", "claude-code"])
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "claude-code" in result.output.lower()
```

Replace with:
```python
def test_doctor_reports_status(tmp_path: Path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init", "--platform", "claude-code"])
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "claude-code" in result.output.lower()
        # Both skills should be reported
        assert "scan=" in result.output.lower() or "scan=true" in result.output.lower()
        assert "cap=" in result.output.lower() or "cap=true" in result.output.lower()
```

Also update `test_uninstall_removes_skills_and_block` to assert the cap skill is gone too. Locate it and replace:
```python
        assert not (Path.cwd() / p.skills_path / "inferspec-scan").exists()
```
with:
```python
        assert not (Path.cwd() / p.skills_path / "inferspec-scan").exists()
        assert not (Path.cwd() / p.skills_path / "inferspec-cap").exists()
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/pytest -v`
Expected: 23 passed.

- [ ] **Step 6: Commit**

```bash
git add src/inferspec/installer.py src/inferspec/cli.py tests/test_cli.py
git -c user.email=anrylu@qnap.com -c user.name=anrylu commit -m "feat(cli): doctor/uninstall/managed-block now aware of both skills"
```

---

## Task 11: Update READMEs (English + 3 translations)

**Files:**
- Modify: `README.md`
- Modify: `README.zh-tw.md`
- Modify: `README.zh-cn.md`
- Modify: `README.ja.md`

- [ ] **Step 1: Update English README**

In `README.md`, locate the section:
```markdown
## Usage

Open your AI agent in the target repo and run:

```
/inferspec-scan
```
```

Replace with:
```markdown
## Usage

Open your AI agent in the target repo. Two skills are available:

**`/inferspec-scan`** — bulk-infer specs for every capability:

```
/inferspec-scan
```

It runs `graphify` to cluster files into capabilities, then for each cap reads
code + `git log` + `docs/` + (if available) Jira/Confluence via MCP + URLs via
the host's WebFetch, and drafts `openspec/specs/<cap>/spec.md` in OpenSpec
format. Drafts may contain `[GAP]` / `[TBD]` markers where the AI was unsure.

**`/inferspec-cap <slug>`** — single-capability deep dive with interactive Q&A:

```
/inferspec-cap user-auth
/inferspec-cap "rate limiting"       # fuzzy match
/inferspec-cap                       # interactive picker
/inferspec-cap new-feature --new     # bootstrap a brand-new cap
```

For one capability, the skill solicits Jira/Confluence/URLs you have, then
asks one focused question per `[GAP]` marker until the spec converges. On
exit it offers to commit the result for you.

Multi-source artefacts are picked up automatically — InferSpec detects MCP
servers in your host environment rather than shipping its own clients.
```

Also update the Status section:
```markdown
## Status

**v0.2 alpha.** Ships `/inferspec-scan` (bulk mode) + `/inferspec-cap`
(interactive single-cap mode). `/inferspec-refine` is under evaluation for
v0.3.
```

- [ ] **Step 2: Mirror the changes to `README.zh-tw.md`, `README.zh-cn.md`, `README.ja.md`**

Translate the Usage and Status sections faithfully into each language. Keep
command examples, flag names, and code blocks untouched (they're language-
agnostic).

For zh-tw, replace the existing Usage section header `## 使用方式` block with
a faithful translation of the new English content. Same for zh-cn (`## 使用方式`)
and ja (`## 使い方`).

For Status:
- zh-tw `## 狀態`: "v0.2 alpha。提供 `/inferspec-scan`（bulk 模式）+ `/inferspec-cap`（互動式單 cap 模式）。`/inferspec-refine` 視 v0.3 評估。"
- zh-cn `## 状态`: "v0.2 alpha。提供 `/inferspec-scan`（bulk 模式）+ `/inferspec-cap`（互动式单 cap 模式）。`/inferspec-refine` 视 v0.3 评估。"
- ja `## ステータス`: "v0.2 alpha。`/inferspec-scan`（bulk モード）+ `/inferspec-cap`（インタラクティブ単一 cap モード）を提供。`/inferspec-refine` は v0.3 で評価。"

- [ ] **Step 3: Verify no `llm-wiki` reintroduction**

Run: `grep -l "llm-wiki" README* docs/ src/ tests/ 2>&1 | grep -v "No such" || echo "clean"`
Expected: `clean`

- [ ] **Step 4: Commit**

```bash
git add README.md README.zh-tw.md README.zh-cn.md README.ja.md
git -c user.email=anrylu@qnap.com -c user.name=anrylu commit -m "docs: README updates for v0.2 (introduce /inferspec-cap)"
```

---

## Task 12: Final verification + tag + push

- [ ] **Step 1: Full suite green**

Run: `.venv/bin/pytest -v 2>&1 | tail -5`
Expected: 23 passed.

- [ ] **Step 2: SKILL.md lint for both skills**

Run:
```bash
.venv/bin/python -c "
import importlib.resources, re
from pathlib import Path

for skill_name in ('inferspec-scan', 'inferspec-cap'):
    p = Path(str(importlib.resources.files('inferspec') / 'skills' / skill_name / 'SKILL.md'))
    text = p.read_text()
    assert text.startswith('---'), f'{skill_name}: missing frontmatter'
    assert re.search(rf'^name:\s*{skill_name}', text, re.M), f'{skill_name}: bad name'
    m = re.search(r'^description:\s*(.+)$', text, re.M)
    assert m and len(m.group(1).strip()) > 20, f'{skill_name}: description too short'
    print(f'{skill_name} SKILL.md OK')
"
```
Expected: two `OK` lines.

- [ ] **Step 3: Real-world smoke test (install both skills into clean tmpdir)**

Run:
```bash
TMP=$(mktemp -d) && cp -r examples/legacy-flask-app "$TMP/demo" && cd "$TMP/demo"
/Users/anrylu/Documents/workspace/infer-spec/.venv/bin/inferspec init --platform claude-code
ls .claude/skills/
ls .claude/skills/inferspec-cap/prompts/
/Users/anrylu/Documents/workspace/infer-spec/.venv/bin/inferspec doctor
/Users/anrylu/Documents/workspace/infer-spec/.venv/bin/inferspec uninstall --yes
cd - && rm -rf "$TMP"
```
Expected:
- Both `inferspec-scan` and `inferspec-cap` directories listed
- 5 prompt files listed for inferspec-cap
- `doctor` reports `scan=True cap=True block=True`
- `uninstall` succeeds; tmpdir cleaned

- [ ] **Step 4: Re-install the global skill (so user can use it immediately)**

Run:
```bash
cd ~ && /Users/anrylu/Documents/workspace/infer-spec/.venv/bin/inferspec init --platform claude-code 2>&1 | tail -3
cd /Users/anrylu/Documents/workspace/infer-spec
```

- [ ] **Step 5: Tag and push**

Run:
```bash
git tag v0.2.0-cap -m "v0.2: /inferspec-cap interactive single-capability Q&A skill"
git log --oneline | head -20
git push origin master
git push origin v0.2.0-cap
```

---

## Self-Review

**Spec coverage (against `2026-05-20-inferspec-cap-design.md`):**

| Spec section | Implemented by task |
|---|---|
| § 1 Positioning + differentiation table | README updates (Task 11), SKILL.md (Task 7) |
| § 2.1 Invocation forms (4 variants) | resolve_cap.md (Task 2) + SKILL.md Usage section (Task 7) |
| § 2.2 Resolution rules (6 ordered cases) | resolve_cap.md (Task 2) |
| § 3.1 Loop structure | SKILL.md Steps 3–6 (Task 7) |
| § 3.2 Question quality rules | ask_gap.md (Task 4) |
| § 3.3 Loop termination | SKILL.md Step 5 (Task 7) |
| § 4 Context gathering | solicit_sources.md (Task 3) + reuse of scan's draft_spec.md (Task 7 Step 3) |
| § 5.1 Output file path/format | SKILL.md Step 6 (Task 7) |
| § 5.2 Footer `last_qa_run` | SKILL.md Step 6 (Task 7) |
| § 5.3 Optional transcript | SKILL.md Step 8 (Task 7) |
| § 6.1 File layout | Tasks 1–7 |
| § 6.2 Shared spec_template | Direct copy in Task 1 (no `_shared/` refactor for v0.2) |
| § 6.3 Installer test update | Task 8 |
| § 7.1 In-scope items | All tasks |
| § 7.3 Success criteria | Task 12 smoke test + manual dogfood |
| § 9 Q1 Direct write | SKILL.md Step 5.4 + rewrite_requirement.md (Tasks 5, 7) |
| § 9 Q2 Single-prompt batch | batch_detect.md (Task 6) + SKILL.md Step 4 (Task 7) |
| § 9 Q3 End-of-session commit | SKILL.md Step 7 (Task 7) |

**Placeholder scan:** None. Every step has concrete code, prompt text, or commands.

**Type/naming consistency:** Slug `inferspec-cap` used identically in SKILL.md
frontmatter, file paths, doctor output, README references. `[GAP]` / `[TBD]` /
`__inferspec_meta__` / `last_qa_run` spelled identically throughout.

**Cross-task ordering:** Tasks 1–7 build the skill (stub → prompts → full
SKILL.md). Task 8 adds unit test. Task 9 extends e2e. Task 10 wires CLI.
Task 11 updates docs. Task 12 ships. Each step is independently testable.

**Deferred to v0.3:**
- `/inferspec-refine` (re-evaluate after dogfooding `/inferspec-cap` in load-existing mode)
- `_shared/spec_template.md` extraction (defer until 3rd skill needs it)
- PyPI release
- Multi-cap parallel Q&A
- Auto-commit policy beyond the single end-of-session prompt
