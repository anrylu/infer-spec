# InferSpec

**Reverse-infer OpenSpec specs from your codebase + git history + docs** —
designed for legacy code that has no spec.

[![CI](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml/badge.svg)](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **From Code & Context to Clear Specs**

## Why InferSpec?

You inherit a 50K-line Flask service. There is no spec. There is a Jira board
from three years ago, a Confluence wiki nobody updates, and the git log.

**InferSpec reads all of it** and produces a structured OpenSpec spec — one
`spec.md` per capability — with each Requirement cited back to `file:line` or
a ticket ID. Ambiguities are marked `[GAP]`/`[TBD]` so you can fill them
interactively in a follow-up pass.

## How it works

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — uvx Python package: installer + CLI               │
│  (never calls an LLM API)                                   │
└─────────────────────────────────────────────────────────────┘
                       │ installs skills into
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — Skills run inside Claude Code / Codex / Gemini   │
│  / Copilot / OpenCode and use the host's subscription AI    │
└─────────────────────────────────────────────────────────────┘
```

InferSpec leans on your existing AI subscription. No API keys, no cloud
endpoints to configure.

## Install

```bash
uvx inferspec init --platform claude-code
```

That drops `/inferspec-scan` into `.claude/skills/` for the current directory.
See `inferspec platforms` for the full list.

## Usage

Open your AI agent in the target repo and run:

```
/inferspec-scan
```

The skill:
1. Runs `graphify` to cluster files into capabilities
2. For each capability, reads code + `git log` + `docs/` + (if available) Jira/Confluence via MCP + URLs via the host's WebFetch
3. Drafts `openspec/specs/<cap>/spec.md` in OpenSpec format

Multi-source artefacts are picked up automatically — InferSpec detects MCP
servers in your host environment rather than shipping its own clients.

## Output format

Same convention as [OpenSpec](https://github.com/Fission-AI/OpenSpec):

```markdown
## Purpose

User authentication for the order portal — replaced the legacy SSO bridge
after incident-1234. See AUTH-456.

## Requirements

### Requirement: Rate Limiting
The system SHALL reject login attempts after 5 failures within 60 seconds.

**Source:** auth.py:18-21, [JIRA AUTH-456]

#### Scenario: Lockout after repeated failures
- **GIVEN** 5 failed attempts in the last minute
- **WHEN** another POST /auth/login arrives
- **THEN** server returns 429
```

## Relationship to llm-wiki-scan

InferSpec writes the same OpenSpec format as `llm-wiki-scan`. The two are
complementary:

| Tool | Best for |
|---|---|
| `llm-wiki-scan` | Bulk seed an entire repo, code-only context |
| InferSpec | Per-capability deep dives with multi-source context + Q&A |

## Status

**v0.1 alpha.** This release ships `/inferspec-scan` (bulk mode). The
interactive `/inferspec-cap` and `/inferspec-refine` skills land in v0.2.

## License

MIT
