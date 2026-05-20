---
name: inferspec-scan
description: Reverse-infer OpenSpec specs from this repo's code + git history + local docs (and Jira/Confluence/URLs if available via MCP or host WebFetch). Triggered by /inferspec-scan.
---

# /inferspec-scan

Bulk-infer OpenSpec specs for every capability in the current repo. Drafts are
written with `[GAP]`/`[TBD]` markers — non-blocking, so even ambiguous code gets
a starting spec. Follow up with `/inferspec-cap` or `/inferspec-refine` (separate
skills) to fill the gaps interactively.

## Output format

Each `openspec/specs/<cap>/spec.md` has two H2 sections — `## Purpose` and
`## Requirements`. Requirements use RFC 2119 keywords (MUST / SHALL / SHOULD /
MAY) and carry `**Source:**` citations. Same convention as `llm-wiki-scan`.

## Usage

```
/inferspec-scan                            # full scan (incremental if previous run exists)
/inferspec-scan --force-rescan             # bypass hash-skip
/inferspec-scan --exclude vendor third_party
```

## When this skill is invoked, run these steps

### Step 0 — Parse flags + read config

Parse the user's invocation for these flags:
- `--force-rescan` → set `FORCE_RESCAN=1`
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

### Step 2 — Classify capabilities

Read `prompts/classify_capabilities.md` (next to this SKILL.md) and follow it.
Output: `graphify-out/features.json`.

Apply `--exclude` and `.inferspec.yaml exclude:` here — drop any capability whose
name contains an excluded keyword.

### Step 3 — Detect available context sources

For each of the following, check whether the host AI has access. Don't fail if
missing — just record what's available:

- **Local docs:** Glob `docs/**/*.md`, `README*`, `CHANGELOG*`, `openspec/specs/**/*.md`
- **Git log:** `git rev-parse --is-inside-work-tree` succeeds → git history is usable
- **Jira MCP:** any tool named `mcp__*__jira_*`? If yes, ask user once:
  "I see a Jira MCP server is available. Should I search for tickets matching
   each capability slug? (y/n)"
- **Confluence MCP:** any tool named `mcp__*__confluence_*`? Same prompt.
- **WebFetch:** if the user volunteers a URL during the scan, use the host's
  WebFetch / browser tool to fetch it. Do NOT scrape unsolicited.

### Step 4 — Per-capability drafting

For each capability in `features.json`:

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
- Find local docs that mention any file in `cap.files` or the cap slug.
- If Jira MCP enabled: search by slug and (optionally) by ticket IDs found in
  commit messages.
- Token budget: cap total context at ~8K tokens per cap. Summarise the older
  half of commits if needed.

#### 4c — Draft spec

Read `prompts/draft_spec.md` and follow it to produce `spec.md` body.

Replace placeholders in `spec_template.md`:
- `{purpose_paragraph_or_tbd}` → drafted Purpose, or `<!-- [TBD: Purpose] -->`
- `{requirements_blocks}` → drafted Requirements
- `{hash}` → sha256 from step 4a
- `{timestamp}` → ISO-8601 UTC current time

Write to `openspec/specs/<cap.name>/spec.md`.

### Step 5 — Report

Output:
```
✓ Scanned <N> capabilities
✓ <M> spec.md files written (<S> skipped via hash)
⚠ <G> [GAP] markers across <C> capabilities — run /inferspec-cap or /inferspec-refine
```

Do NOT auto-commit. Leave that to the user.

## Notes for the host AI

- This skill never calls a cloud LLM API. You ARE the LLM — execute the prompts
  inline in this session.
- Per-capability drafting is independent. If processing one cap fails, log it
  and continue with the next.
- Source citations are mandatory. A Requirement with no `**Source:**` is a bug.
- `[GAP]` markers are a FEATURE, not a failure. They power the refine workflow.
