# InferSpec — Design (v0.1)

**Status:** Draft for v0.1 MVP
**Date:** 2026-05-20
**Author:** anrylu
**References:** `~/Documents/workspace/soul-forge`

---

## 1. Positioning

InferSpec is an open-source tool that **reverse-infers structured specs from existing codebases and surrounding artefacts** (git history, local docs, optionally Jira/Confluence via MCP, optionally URLs via host AI's WebFetch). It outputs OpenSpec-format Markdown (`openspec/specs/<cap>/spec.md`).

### Differentiation

- **Bulk + per-cap + incremental** modes — onboard a new repo or deep-dive a single capability
- **Multi-source context** — code + git history + local docs + MCP-detected Jira/Confluence + WebFetch via host AI
- **Interactive Q&A loop** — the skill asks targeted questions when ambiguity is detected, instead of producing static drafts only

### Tagline

> **InferSpec — From Code & Context to Clear Specs**

---

## 2. Architecture

### 2.1 Two-layer split (mirrors soul-forge)

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — uvx Python package (inferspec)                   │
│    • Installer / scaffolding / local utilities              │
│    • NEVER calls an LLM API                                 │
└─────────────────────────────────────────────────────────────┘
                            │ installs into
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — Skills (Claude Code / Codex / Gemini / Copilot)  │
│    • Real execution logic, runs in the host AI session      │
│    • Uses the host's subscription LLM (no API keys needed)  │
│    • Calls host tools to read files, run graphify, MCP, web │
└─────────────────────────────────────────────────────────────┘
```

This is the same model `soul-forge` uses. The Python side is intentionally thin — it never sees the LLM.

### 2.2 Repo structure

```
infer-spec/
├── README.md / README.zh-tw.md / README.ja.md
├── pyproject.toml                  # uvx-installable, name=inferspec
├── src/inferspec/
│   ├── cli.py                      # `inferspec init` / `doctor` / `uninstall`
│   ├── installer.py                # writes skills into host CLI configs
│   ├── platforms.py                # claude-code / codex / gemini / copilot paths
│   ├── managed_block.py            # idempotent install (port from soul-forge)
│   └── skills/                     # bundled skill markdown templates
│       ├── inferspec-scan/SKILL.md
│       ├── inferspec-cap/SKILL.md
│       ├── inferspec-refine/SKILL.md
│       └── _shared/                # prompts, OpenSpec templates, helpers
├── tests/
├── examples/
│   ├── legacy-flask-app/
│   └── microservice-go/
└── docs/superpowers/
    ├── specs/                      # this doc lives here
    └── plans/                      # implementation plans
```

### 2.3 Three skills

| Skill | Trigger | Scope | Interactivity |
|---|---|---|---|
| `/inferspec-scan` | Bulk first-run | Whole repo → all capabilities | Low (only on critical ambiguity) |
| `/inferspec-cap <slug>` | Single-cap deep dive | One capability, all sources | High (active Q&A loop) |
| `/inferspec-refine [cap]` | Iterative gap-fill | Existing `spec.md`, find `[TBD]`/`[GAP]` markers | Medium (per-gap question) |

The split lets users pick the right tool for the job: onboard a new repo (scan), document a critical feature thoroughly (cap), keep specs fresh as code evolves (refine).

### 2.4 Core pipeline (shared)

```
[Input: repo path + optional cap slug]
        │
        ▼
Stage 1: Code Understanding (graphify, PyPI public)
        • AST extract → graph.json
        • Community detect → features.json (capability groups)
        │
        ▼
Stage 2: Context Collection
        • Local: docs/, README, git log/blame, openspec/
        • MCP: detect Jira/Confluence/GitLab MCP servers → call if available
        • Web: host AI's WebFetch tool for URLs the user pastes
        │
        ▼
Stage 3: LLM Spec Drafting (host's subscription AI)
        • Per-cap prompt with collected context
        • Marks unknowns as [GAP]/[TBD]
        • Writes OpenSpec-format spec.md
        │
        ▼
Stage 4: Interactive Q&A (cap/refine modes only)
        • Find [GAP] markers
        • Ask user to fill
        • Rewrite affected Requirement inline
        │
        ▼
[Output: openspec/specs/<cap>/spec.md + graphify-out/]
```

### 2.5 MCP detection

InferSpec never ships its own Jira/Confluence client. Instead, each skill queries the host environment:

```
Tools available include `mcp__*__jira_*` or `mcp__*__confluence_*`?
  ├─ Yes → Prompt user: "Detected Jira MCP. Pull related tickets for cap X?"
  └─ No  → Skip silently, use local sources only
```

Adding a new source = adding a "if tool available, do X" branch in the prompt. No InferSpec release needed.

---

## 3. Data flow & OpenSpec alignment

### 3.1 OpenSpec convention

Each `openspec/specs/<cap>/spec.md` has exactly two H2 sections:

```markdown
## Purpose

<PM-intent, 1–2 paragraphs. InferSpec extracts "why" from git commits,
 PRs, and Jira tickets — not just "what" the code does.>

## Requirements

### Requirement: User Authentication
The system SHALL authenticate users via email + password.

**Source:** src/auth/login.py:42-89, [JIRA AUTH-123]

#### Scenario: Successful login
- **GIVEN** valid credentials
- **WHEN** POST /login is called
- **THEN** server returns 200 with session token

#### Scenario: Rate limiting
- **GIVEN** 5 failed attempts within 1 minute
- **WHEN** another login attempt arrives
- **THEN** server returns 429  <!-- [GAP: limit value inferred, confirm] -->
```

Rules:
- RFC 2119 keywords: MUST / SHALL / SHOULD / MAY
- Every Requirement carries a `**Source:**` line pointing at `file:line` and/or ticket IDs
- `<!-- [GAP: ...] -->` marks values inferred but unverified — Q&A loop targets these
- `<!-- [TBD: Purpose] -->` marks empty Purpose for refine mode

### 3.2 Mode flows

**Mode A — `/inferspec-scan` (bulk, non-blocking):**

```
repo → graphify → features.json (N caps)
for each cap:
    collect: code files + git log <files> + matched docs/*.md
    optional: if MCP Jira available → search by cap slug
    LLM prompt → draft spec.md (with [GAP]/[TBD])
    write openspec/specs/<cap>/spec.md
report: N caps written, M gaps remaining, suggest /inferspec-refine
```

Never blocks. Drafts get committed even with gaps.

**Mode B — `/inferspec-cap <slug>` (deep, interactive):**

```
locate cap in features.json (or infer from user description)
collect Mode A sources + actively ask:
    "Any Jira ticket / Confluence page / URL for this cap?"
LLM drafts → finds ambiguity → asks:
    "src/auth.py:67 has a rate limiter but I don't see the limit
     configured. Is it the default, or am I missing a config file?"
user answers → LLM rewrites that Requirement
loop until no [GAP] markers or user says "enough"
write openspec/specs/<cap>/spec.md
```

**Mode C — `/inferspec-refine [cap]`:**

```
read existing openspec/specs/<cap>/spec.md
grep [GAP] / [TBD] markers
for each marker: run Q&A loop (same as Mode B)
rewrite spec.md
```

### 3.3 Git history (a core InferSpec value-add)

For each cap's file list:

```bash
git log --follow --no-merges --pretty='%H%n%s%n%b%n---' -- <files>
git log --all --grep='<cap-slug>' --pretty='%s%n%b'
```

Commit messages frequently encode intent that source code can't show:
- Why a feature exists (`feat: add rate limiting because of incident-1234`)
- Linked tickets (`AUTH-456: handle expired tokens`)
- Edge cases (`fix: edge case when user has 2 sessions`)

InferSpec surfaces these as Purpose paragraphs and Source citations.

### 3.4 Hash-skip incremental

Each spec.md ends with:

```html
<!-- __inferspec_meta__: {"hash": "<sha256-of-source-files>", "scan_ts": "2026-05-20T..."} -->
```

On next run, the skill recomputes the hash from the cap's source files. If unchanged, skip. `--force-rescan` overrides.

### 3.5 Output layout

```
<repo>/
├── openspec/
│   └── specs/
│       ├── user-auth/spec.md
│       ├── order-management/spec.md
│       └── ...
├── graphify-out/            # .gitignored
│   ├── graph.json
│   └── features.json
└── .inferspec.yaml          # optional config
```

`.inferspec.yaml` (optional):

```yaml
name: my-app
exclude: [vendor, third_party]
cap_aliases:
  auth: user-authentication   # rename cap slug
mcp_overrides:
  jira: false                 # disable detected MCP even if present
```

`.inferspec.yaml` is scoped to InferSpec and does not conflict with other tools' config files.

---

## 4. MVP (v0.1) scope

### 4.1 In scope

- **uvx package** `inferspec` (PyPI) with installers for Claude Code, Codex, Gemini CLI, Copilot CLI, OpenCode (port from soul-forge)
- **CLI:** `inferspec init`, `inferspec doctor`, `inferspec uninstall`
- **Three skills:** `/inferspec-scan`, `/inferspec-cap`, `/inferspec-refine`
- **graphify integration:** auto-install, run, produce `graphify-out/{graph.json, features.json}`
- **Local sources:** code files, git log/blame, `docs/`, `README.md`, `CHANGELOG.md`, existing `openspec/`
- **MCP detection:** detect `mcp__*__jira_*` / `mcp__*__confluence_*`; use if present, skip cleanly if not
- **WebFetch fallback:** rely on host AI's own web-fetch tool
- **OpenSpec output:** `openspec/specs/<cap>/spec.md` with Source attribution and `[GAP]`/`[TBD]` markers
- **Q&A loop:** active in `cap` and `refine` modes only
- **Hash-skip incremental:** `__inferspec_meta__` footer
- **Examples:** ≥2 demo targets (one Python, one Go or TS)
- **Tests:** installer / CLI / OpenSpec parser unit tests

### 4.2 Out of scope (v0.2+)

| Item | Reason |
|---|---|
| Own Jira/Confluence/GitLab API client | Delegated to host MCP servers — InferSpec doesn't manage tokens |
| URL scraper | Delegated to host AI's WebFetch |
| Web dashboard / UI | Originally tagged V2 in the user's roadmap |
| Multi-format export (JSON Schema, OpenAPI, Gherkin) | OpenSpec is source-of-truth; add `inferspec export` in v0.2 |
| Bedrock / cloud LLM API | Violates "use host subscription" principle |
| Auto-commit / auto-PR | Leave to user |
| Spec-vs-code drift detection | v0.3 |
| Localized prompts (zh/ja) | v0.1 prompts in English; AI responds in user's language |

### 4.3 Success criteria

v0.1 ships when:

1. `uvx inferspec init` successfully installs skills on at least 1 of Claude Code / Codex / Gemini CLI
2. `/inferspec-scan` on `examples/legacy-flask-app/` produces valid OpenSpec `openspec/specs/*/spec.md`
3. `/inferspec-cap <slug>` triggers a Q&A loop at least once; user answer rewrites spec correctly
4. MCP detection in an environment without Jira MCP skips cleanly (no errors)
5. CI green, README includes a demo asciinema or GIF
6. ≥2 outside testers run it end-to-end and judge the spec output as reasonable

### 4.4 Risks & mitigations

| Risk | Mitigation |
|---|---|
| Skill paths/formats vary across host CLIs | Reuse soul-forge's `platforms.py` abstraction |
| graphify language coverage uncertain (Rust, Kotlin) | Pick verified languages for examples; document supported langs |
| Long-prompt LLM inconsistency | Per-cap drafting (no single mega-prompt); explicit OpenSpec schema constraints in prompt |
| `[GAP]` markers ignored and pile up | `inferspec doctor` counts open gaps and warns |

---

## 5. Development sequence

| Week | Goal | Deliverable |
|---|---|---|
| 1 | Repo bootstrap + port soul-forge `installer.py` | `uvx inferspec init` installs an empty skill into Claude Code |
| 2 | OpenSpec template + graphify integration script | `/inferspec-scan` produces `graph.json` on a demo repo |
| 3 | `/inferspec-scan` full prompt + spec.md generation | Drafts (with `[GAP]` markers) on Flask demo |
| 4 | Git log integration + Source attribution | spec.md has `**Source:**` lines pointing to file:line / commit |
| 5 | `/inferspec-cap` deep mode + Q&A loop | Interactive spec drafting converges correctly |
| 6 | `/inferspec-refine` + MCP detection | Auto-pulls Jira context when MCP is present |
| 7 | Multi-platform installers (Codex / Gemini / Copilot) + hash-skip | All target platforms install cleanly |
| 8 | Examples, README, docs, demo GIF, PyPI release | Public v0.1 |

Weeks 1+2 can run in parallel. Weeks 4–5 are strongly coupled, do in sequence.

---

## 6. Evaluation of graphify

**Verdict: use it.**

`graphify` (PyPI: `graphifyy`) already does the AST → cluster → JSON pipeline that legacy-codebase analysis depends on. For a tool whose value rests on grouping unfamiliar files into meaningful capabilities, this is the most expensive piece to reinvent.

What InferSpec adds on top of graphify:
- A **multi-source context linker** that maps non-code artefacts (commit messages, Jira tickets, docs) onto the graph's nodes
- An **interactive Q&A layer** that targets ambiguity flagged during spec drafting
- A **host-tool integration layer** (MCP detect, WebFetch passthrough)

The graph itself stays as graphify's output. InferSpec is the orchestration + reasoning + UX layer above it.

---

## 7. Open questions (resolved in clarification)

- ✅ Form factor: uvx installer + per-platform skills (no own LLM API, lean on host subscription)
- ✅ Sources for MVP: local only (code, git, docs); external sources via MCP detection + host WebFetch
- ✅ Output format: OpenSpec
- ✅ Q&A model: skill actively asks during inference; user can also correct anytime

---

## 8. Non-goals (to prevent scope creep)

- Not a continuous-integration / drift-detection product (yet)
- Not opinionated about how teams version their specs
- Not building a hosted service
