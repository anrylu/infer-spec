---
name: inferspec-scan
description: Reverse-infer OpenSpec specs from this repo's code + git history + local docs (and Jira/Confluence/URLs if available via MCP or host WebFetch). Triggered by /inferspec-scan.
---

# /inferspec-scan

Bulk-infer OpenSpec specs for every capability in the current repo. Drafts are
written with `[GAP]`/`[TBD]` markers — non-blocking, so even ambiguous code gets
a starting spec. Follow up with `/inferspec-cap <slug>` to fill the gaps
interactively (it also handles iterative gap-fill on existing specs).

## Output format

Each `openspec/specs/<cap>/spec.md` has two H2 sections — `## Purpose` and
`## Requirements`. Requirements use RFC 2119 keywords (MUST / SHALL / SHOULD /
MAY) and carry `**Source:**` citations.

## Usage

```
/inferspec-scan                            # full scan (incremental if previous run exists)
/inferspec-scan --force-rescan             # bypass hash-skip
/inferspec-scan --since HEAD~20            # only re-draft caps whose files changed since <rev>
/inferspec-scan --exclude vendor third_party
```

## When this skill is invoked, run these steps

### Step 0 — Parse flags + read config

Parse the user's invocation for these flags:
- `--force-rescan` → set `FORCE_RESCAN=1`
- `--since <rev>` → set `SINCE_REV=<rev>` (used in Step 4 to filter caps)
- `--exclude <name> [<name>...]` → collect excludes

Read `.inferspec.yaml` from cwd if present. Use its `exclude:` list additively
with the CLI `--exclude`. Use its `mcp_overrides:` to disable detected MCP
servers the user wants to skip.

Ensure `graphify-out/` is gitignored:
```bash
if [ -f .gitignore ] && ! grep -qxF "graphify-out/" .gitignore; then
    echo "graphify-out/" >> .gitignore
fi
```

### Step 0.5 — Load glossary (do-not-translate list)

If `.inferspec-glossary.txt` exists in cwd, read it. Each non-comment, non-empty
line is a term that MUST appear verbatim in spec output — no translation, no
case change, no expansion. Typical entries: product names, internal acronyms,
canonical service names (e.g. `myQNAPcloud`, `QID`, `tunnel-service`).

If the file is missing, fall back to a minimal built-in list:

```
# Inferred from repo name + common framework names. Override by creating .inferspec-glossary.txt.
OpenSpec
MCP
```

Inject the resolved glossary into `prompts/draft_spec.md` rendering as a
`Glossary:` block. Audit the drafted spec body — if a glossary term appears
translated or rewritten, re-draft that Requirement.

### Step 1 — Run graphify

Install `graphifyy` if missing:
```bash
python3 -c "import graphify" 2>/dev/null || pip install graphifyy -q --break-system-packages
```

Run graphify to produce `graphify-out/graph.json`:
```bash
python3 -c "
from graphify.detect import detect
from graphify.extract import collect_files, extract
from graphify.build import build_from_json
from graphify.cluster import cluster
from graphify.export import to_json
from pathlib import Path

result = detect(Path('.'))
code_files = []
for f in result.get('files', {}).get('code', []):
    p = Path(f)
    code_files.extend(collect_files(p) if p.is_dir() else [p])
extraction = extract(code_files)
G = build_from_json(extraction)
communities = cluster(G)
to_json(G, communities, 'graphify-out/graph.json')
print(f'Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')
"
```

If `total_files > 5000`, warn user to add a `.graphifyignore`.

### Step 2 — Classify capabilities (+ API-spec detection)

Read `prompts/classify_capabilities.md` (next to this SKILL.md) and follow it.
Output: `graphify-out/features.json`.

**Then enrich with API-spec capabilities.** Search the repo for OpenAPI /
Swagger documents:

```bash
find . -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) \
  \( -path '*/api/*' -o -path '*/apis/*' -o -path '*/openapi/*' \
     -o -path '*/swagger/*' -o -path '*/spec/*' -o -path '*/specs/*' \
     -o -path '*/doc/*' -o -path '*/docs/*' -o -path '*/res/swagger/*' \) \
  2>/dev/null | head -200
```

For each candidate, peek the first 80 lines. Keep the file if it contains an
`openapi:`/`swagger:` top-level key (YAML) or `"openapi"`/`"swagger"` at the
JSON root, **or** a `paths:` / `"paths"` block. Group keepers by directory; each
group becomes a synthetic capability named after the directory's basename
(prefix with `api-` if not already). Append to `features.json` with the spec
files as `cap.files`.

Apply `--exclude` and `.inferspec.yaml exclude:` here — drop any capability whose
name contains an excluded keyword.

### Step 3 — Detect available context sources

For each of the following, check whether the host AI has access. Don't fail if
missing — just record what's available:

- **Local docs (design specs):** glob the following in priority order and keep
  results that exist:
  - `docs/superpowers/specs/**/*.md`
  - `docs/superpowers/plans/**/*.md`
  - `docs/specs/**/*.md`
  - `docs/design/**/*.md`
  - `docs/**/*.md`
  - `README*`, `CHANGELOG*`
  - `openspec/specs/**/*.md` (existing specs — preserve PM-authored Requirements)
- **Git log:** `git rev-parse --is-inside-work-tree` succeeds → git history is usable
- **Jira MCP:** any tool named `mcp__*__jira_*`? If yes, ask user once:
  "I see a Jira MCP server is available. Should I search for tickets matching
   each capability slug? (y/n)"
- **Confluence MCP:** any tool named `mcp__*__confluence_*`? Same prompt.
- **WebFetch:** if the user volunteers a URL during the scan, use the host's
  WebFetch / browser tool to fetch it. Do NOT scrape unsolicited.

### Step 4 — Per-capability drafting

If `SINCE_REV` is set, run `git diff --name-only <SINCE_REV>...HEAD` first and
build a set of changed files. Skip any capability whose `cap.files` does NOT
intersect that set (record as `skipped-incremental`).

For each remaining capability in `features.json`:

#### 4a — Hash-skip check

Compute `sha256` over the concatenated contents of `cap.files` (sorted order).
Read existing `openspec/specs/<cap.name>/spec.md` if present and parse the
`__inferspec_meta__` footer. If `hash` matches and `FORCE_RESCAN` is not set,
skip this capability.

#### 4b — Gather context

- Read every file in `cap.files`.
- Run `git log --follow --no-merges --pretty='%H%n%s%n%b%n---' -- <files>` and
  collect commits. Cap at 50 most recent.
- Run `git log --all --grep='<cap.name>' --pretty='%s%n%b'` for slug mentions.
- **Match design docs.** For each doc collected in Step 3, score relevance by:
  (a) filename contains cap slug → +2; (b) doc body mentions any file in
  `cap.files` → +1 per file (capped at +5); (c) doc body mentions the cap
  slug or any of its split tokens → +1 each (capped at +3). Keep the top 3
  scoring docs (score ≥ 2). Include their content (or excerpts if >2K tokens
  each) in the drafting prompt.
- If Jira MCP enabled: search by slug and (optionally) by ticket IDs found in
  commit messages.
- Token budget: cap total context at ~8K tokens per cap. Summarise the older
  half of commits if needed; truncate doc excerpts before commits.

#### 4c — Draft spec

Read `prompts/draft_spec.md` and follow it to produce `spec.md` body. Pass
the glossary from Step 0.5 as a `Glossary:` block in the prompt.

Replace placeholders in `spec_template.md`:
- `{purpose_paragraph_or_tbd}` → drafted Purpose, or `<!-- [TBD: Purpose] -->`
- `{requirements_blocks}` → drafted Requirements
- `{hash}` → sha256 from step 4a
- `{timestamp}` → ISO-8601 UTC current time

Write to `openspec/specs/<cap.name>/spec.md`.

### Step 5 — Detect removals + report

Compare the current `features.json` cap-slug set against the previous run's
cap set (read from `graphify-out/.last-features.json` if present). For each
slug present last time but missing now, do NOT delete the existing
`openspec/specs/<slug>/spec.md`. Instead, draft a deprecation proposal at
`openspec/changes/auto-remove-<slug>-<YYYYMMDD>.md`:

```markdown
# Proposal: Remove capability `<slug>`

The `/inferspec-scan` clustering no longer identifies `<slug>` as a distinct
capability. This may mean the code was merged into another cap, removed
entirely, or simply re-clustered. **Review before deleting** the spec at
`openspec/specs/<slug>/spec.md`.

Last seen: <previous-run-timestamp>
Files last associated: <list from previous features.json>
```

After all caps are processed, write the new `features.json` to
`graphify-out/.last-features.json` for next run.

Output:
```
✓ Scanned <N> capabilities (<I> skipped via --since, <S> via hash)
✓ <M> spec.md files written
⚠ <G> [GAP] markers across <C> capabilities — run /inferspec-cap <slug> to fill them
⚠ <R> removal proposals drafted under openspec/changes/ — review before deleting specs
```

Do NOT auto-commit. Leave that to the user.

## Notes for the host AI

- This skill never calls a cloud LLM API. You ARE the LLM — execute the prompts
  inline in this session.
- Per-capability drafting is independent. If processing one cap fails, log it
  and continue with the next.
- Source citations are mandatory. A Requirement with no `**Source:**` is a bug.
- `[GAP]` markers are a FEATURE, not a failure. `/inferspec-cap <slug>` resolves
  them interactively, including against an existing draft.
- Glossary terms MUST appear verbatim. Re-draft any Requirement where a
  glossary term was translated or paraphrased.
