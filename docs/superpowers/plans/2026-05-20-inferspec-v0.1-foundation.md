# InferSpec v0.1 Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `/inferspec-scan` end-to-end — uvx-installable package that drops a working scan skill into Claude Code and produces OpenSpec drafts on a demo repo.

**Architecture:** Two layers — a thin Python uvx package (installer/CLI only, no LLM calls) and bundled Markdown skill templates (`/inferspec-scan`) that the host AI executes in-session. Code understanding via `graphify` (PyPI public lib).

**Tech Stack:** Python 3.12+, `hatchling`, `click`, `rich`, `pyyaml`, `pytest`. `graphifyy` invoked at skill runtime (not a Python dep of the package itself).

**Scope cut:** This plan covers Weeks 1–4 of the design doc — foundation, installer, `/inferspec-scan`, git log + Source attribution, hash-skip incremental, demo, README. Subsequent plans (`/inferspec-cap`, `/inferspec-refine`, multi-platform installers, PyPI release) are separate documents.

**Spec reference:** `docs/superpowers/specs/2026-05-20-inferspec-design.md`

---

## File Structure

```
infer-spec/
├── pyproject.toml                              # CREATE — uvx-installable
├── README.md                                   # CREATE
├── .gitignore                                  # CREATE
├── .github/workflows/ci.yml                    # CREATE — pytest matrix
├── src/inferspec/
│   ├── __init__.py                             # CREATE
│   ├── cli.py                                  # CREATE — init/doctor/uninstall
│   ├── installer.py                            # CREATE — port from soul-forge
│   ├── platforms.py                            # CREATE — port from soul-forge
│   ├── managed_block.py                        # CREATE — port from soul-forge
│   └── skills/
│       └── inferspec-scan/
│           ├── SKILL.md                        # CREATE — full skill prompt
│           ├── spec_template.md                # CREATE — OpenSpec skeleton
│           └── prompts/
│               ├── classify_capabilities.md    # CREATE
│               └── draft_spec.md               # CREATE
├── tests/
│   ├── __init__.py                             # CREATE
│   ├── test_managed_block.py                   # CREATE
│   ├── test_platforms.py                       # CREATE
│   ├── test_installer.py                       # CREATE
│   ├── test_cli.py                             # CREATE
│   └── fixtures/
│       └── tiny_repo/                          # CREATE — minimal target
└── examples/
    └── legacy-flask-app/                       # CREATE — demo target
        ├── README.md
        ├── app.py
        └── auth.py
```

**Responsibility split:**
- `platforms.py` — pure data, where each host CLI expects skills/config
- `managed_block.py` — idempotent text-block insertion in a managed file (CLAUDE.md etc.)
- `installer.py` — copies skill bundles into the right platform path; uses `managed_block`
- `cli.py` — `click` wrapper that calls installer
- `skills/inferspec-scan/SKILL.md` — the actual logic the host AI runs

---

## Task 1: Repo bootstrap

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/inferspec/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Write `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
dist/
build/
*.egg-info/
.DS_Store
graphify-out/
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "inferspec"
version = "0.1.0a0"
description = "Reverse-infer OpenSpec specs from code + multi-source context"
readme = "README.md"
requires-python = ">=3.12"
license = "MIT"
authors = [{ name = "anrylu" }]
keywords = ["spec", "openspec", "ai", "agent", "claude", "gemini", "copilot", "legacy-code"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Documentation",
]
dependencies = [
    "click>=8.1",
    "rich>=13.0",
    "pyyaml>=6.0",
]

[project.urls]
Homepage = "https://github.com/anrylu/infer-spec"
Repository = "https://github.com/anrylu/infer-spec"
Issues = "https://github.com/anrylu/infer-spec/issues"

[project.scripts]
inferspec = "inferspec.cli:cli"

[tool.hatch.build.targets.wheel]
packages = ["src/inferspec"]

[tool.hatch.build.targets.wheel.force-include]
"src/inferspec/skills" = "inferspec/skills"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[dependency-groups]
dev = [
    "pytest>=8.0",
]
```

- [ ] **Step 3: Create empty `__init__.py` files**

`src/inferspec/__init__.py`:
```python
__version__ = "0.1.0a0"
```

`tests/__init__.py`: empty file.

- [ ] **Step 4: Verify install works**

Run: `python -m venv .venv && .venv/bin/pip install -e ".[dev]" 2>&1 | tail -5`
Expected: `Successfully installed inferspec-0.1.0a0` (or similar)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore src/inferspec/__init__.py tests/__init__.py
git commit -m "chore: bootstrap inferspec Python package"
```

---

## Task 2: Port `managed_block.py` (idempotent text block)

**Files:**
- Create: `src/inferspec/managed_block.py`
- Create: `tests/test_managed_block.py`

- [ ] **Step 1: Write the failing test**

`tests/test_managed_block.py`:
```python
from pathlib import Path
import pytest

from inferspec.managed_block import write_block, read_block, START_MARKER, END_MARKER


def test_write_block_creates_file(tmp_path: Path):
    f = tmp_path / "CONFIG.md"
    write_block(f, "hello")
    text = f.read_text()
    assert START_MARKER in text
    assert END_MARKER in text
    assert "hello" in text


def test_write_block_replaces_existing(tmp_path: Path):
    f = tmp_path / "CONFIG.md"
    write_block(f, "first")
    write_block(f, "second")
    text = f.read_text()
    assert "first" not in text
    assert "second" in text
    assert text.count(START_MARKER) == 1


def test_write_block_preserves_other_content(tmp_path: Path):
    f = tmp_path / "CONFIG.md"
    f.write_text("# Manual content\n\nKeep me.\n")
    write_block(f, "added")
    text = f.read_text()
    assert "Manual content" in text
    assert "Keep me." in text
    assert "added" in text


def test_read_block_none_when_missing(tmp_path: Path):
    assert read_block(tmp_path / "nonexistent.md") is None


def test_read_block_returns_content(tmp_path: Path):
    f = tmp_path / "CONFIG.md"
    write_block(f, "payload-text")
    assert read_block(f) == "payload-text"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_managed_block.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'inferspec.managed_block'`

- [ ] **Step 3: Write minimal implementation**

`src/inferspec/managed_block.py`:
```python
from pathlib import Path
import re

START_MARKER = "<!-- INFERSPEC:START -->"
END_MARKER = "<!-- INFERSPEC:END -->"

_BLOCK_PATTERN = re.compile(
    re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
    re.DOTALL,
)


def write_block(file_path: Path, content: str) -> None:
    new_block = f"{START_MARKER}\n{content}\n{END_MARKER}"

    if file_path.exists():
        text = file_path.read_text()
        if START_MARKER in text:
            text = _BLOCK_PATTERN.sub(new_block, text)
        else:
            text = text.rstrip() + "\n\n" + new_block + "\n"
    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        text = new_block + "\n"

    file_path.write_text(text)


def read_block(file_path: Path) -> str | None:
    if not file_path.exists():
        return None

    text = file_path.read_text()
    match = _BLOCK_PATTERN.search(text)
    if not match:
        return None

    block = match.group(0)
    return block[len(START_MARKER) : -len(END_MARKER)].strip()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_managed_block.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/inferspec/managed_block.py tests/test_managed_block.py
git commit -m "feat: idempotent managed text block helper"
```

---

## Task 3: Platforms registry

**Files:**
- Create: `src/inferspec/platforms.py`
- Create: `tests/test_platforms.py`

- [ ] **Step 1: Write the failing test**

`tests/test_platforms.py`:
```python
from inferspec.platforms import (
    Platform,
    PLATFORMS,
    get_platform,
    get_platforms_by_ids,
)


def test_platforms_includes_claude_code():
    p = get_platform("claude-code")
    assert p is not None
    assert p.name == "Claude Code"
    assert "claude" in p.skills_path.lower()


def test_get_platform_unknown_returns_none():
    assert get_platform("does-not-exist") is None


def test_get_platforms_by_ids_filters_unknown():
    out = get_platforms_by_ids(["claude-code", "bogus", "gemini-cli"])
    ids = [p.id for p in out]
    assert ids == ["claude-code", "gemini-cli"]


def test_all_platforms_have_distinct_ids():
    ids = [p.id for p in PLATFORMS]
    assert len(ids) == len(set(ids))


def test_platform_is_frozen_dataclass():
    p = Platform(
        id="x", name="X", skills_path=".x/skills", config_file="X.md"
    )
    import dataclasses
    with __import__("pytest").raises(dataclasses.FrozenInstanceError):
        p.id = "y"  # type: ignore[misc]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_platforms.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'inferspec.platforms'`

- [ ] **Step 3: Write the implementation**

`src/inferspec/platforms.py`:
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Platform:
    id: str
    name: str
    skills_path: str
    config_file: str


PLATFORMS: list[Platform] = [
    Platform(
        id="claude-code",
        name="Claude Code",
        skills_path=".claude/skills",
        config_file="CLAUDE.md",
    ),
    Platform(
        id="gemini-cli",
        name="Gemini CLI",
        skills_path=".gemini/skills",
        config_file="GEMINI.md",
    ),
    Platform(
        id="codex",
        name="Codex",
        skills_path=".codex/skills",
        config_file="AGENTS.md",
    ),
    Platform(
        id="github-copilot",
        name="GitHub Copilot",
        skills_path=".github/copilot/skills",
        config_file=".github/copilot-instructions.md",
    ),
    Platform(
        id="opencode",
        name="OpenCode",
        skills_path=".opencode/skills",
        config_file="AGENTS.md",
    ),
]


def get_platform(platform_id: str) -> Platform | None:
    for p in PLATFORMS:
        if p.id == platform_id:
            return p
    return None


def get_platforms_by_ids(ids: list[str]) -> list[Platform]:
    return [p for pid in ids if (p := get_platform(pid)) is not None]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_platforms.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/inferspec/platforms.py tests/test_platforms.py
git commit -m "feat: platforms registry for 5 host CLIs"
```

---

## Task 4: Installer — copy skill bundles into host CLI paths

**Files:**
- Create: `src/inferspec/installer.py`
- Create: `src/inferspec/skills/inferspec-scan/SKILL.md` (stub for now, expanded in Task 6)
- Create: `tests/test_installer.py`

- [ ] **Step 1: Write a stub SKILL.md so the installer has something to copy**

`src/inferspec/skills/inferspec-scan/SKILL.md`:
```markdown
---
name: inferspec-scan
description: Reverse-infer OpenSpec specs from this repo's code + git history + local docs. Triggered by /inferspec-scan.
---

# /inferspec-scan

Placeholder — full skill content lands in Task 6.
```

- [ ] **Step 2: Write the failing test**

`tests/test_installer.py`:
```python
from pathlib import Path

from inferspec.installer import install_platform
from inferspec.platforms import get_platform
from inferspec.managed_block import START_MARKER


def test_install_creates_skills_directory(tmp_path: Path):
    p = get_platform("claude-code")
    assert p is not None
    install_platform(tmp_path, p)

    skill_md = tmp_path / p.skills_path / "inferspec-scan" / "SKILL.md"
    assert skill_md.exists()
    assert "name: inferspec-scan" in skill_md.read_text()


def test_install_writes_managed_block(tmp_path: Path):
    p = get_platform("claude-code")
    install_platform(tmp_path, p)

    config = tmp_path / p.config_file
    assert config.exists()
    text = config.read_text()
    assert START_MARKER in text
    assert "inferspec" in text.lower()


def test_install_is_idempotent(tmp_path: Path):
    p = get_platform("claude-code")
    install_platform(tmp_path, p)
    install_platform(tmp_path, p)

    config = (tmp_path / p.config_file).read_text()
    assert config.count(START_MARKER) == 1


def test_install_preserves_existing_config(tmp_path: Path):
    p = get_platform("claude-code")
    config = tmp_path / p.config_file
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("# Existing content\n\nUser custom notes.\n")

    install_platform(tmp_path, p)

    text = config.read_text()
    assert "Existing content" in text
    assert "User custom notes." in text
    assert START_MARKER in text
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_installer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'inferspec.installer'`

- [ ] **Step 4: Write the implementation**

`src/inferspec/installer.py`:
```python
import importlib.resources
import shutil
from pathlib import Path

from inferspec.managed_block import write_block
from inferspec.platforms import Platform


def _bundled_skills_dir() -> Path:
    return Path(str(importlib.resources.files("inferspec") / "skills"))


def _managed_block_content() -> str:
    return (
        "# InferSpec\n"
        "\n"
        "This repo has InferSpec skills installed. Available slash commands:\n"
        "\n"
        "- `/inferspec-scan` — bulk-infer OpenSpec specs from code + git + docs\n"
        "\n"
        "Specs are written to `openspec/specs/<cap>/spec.md`.\n"
        "See https://github.com/anrylu/infer-spec for docs.\n"
    )


def install_platform(project_dir: Path, platform: Platform) -> None:
    skills_root = project_dir / platform.skills_path
    skills_root.mkdir(parents=True, exist_ok=True)

    src_root = _bundled_skills_dir()
    for skill_dir in sorted(p for p in src_root.iterdir() if p.is_dir()):
        dest = skills_root / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)

    config_file = project_dir / platform.config_file
    config_file.parent.mkdir(parents=True, exist_ok=True)
    write_block(config_file, _managed_block_content())
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_installer.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/inferspec/installer.py src/inferspec/skills/inferspec-scan/SKILL.md tests/test_installer.py
git commit -m "feat: installer copies skill bundles into host CLI paths"
```

---

## Task 5: CLI — `inferspec init`, `doctor`, `uninstall`

**Files:**
- Create: `src/inferspec/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

`tests/test_cli.py`:
```python
from pathlib import Path

from click.testing import CliRunner

from inferspec.cli import cli
from inferspec.platforms import get_platform
from inferspec.managed_block import START_MARKER


def test_platforms_command_lists_all():
    runner = CliRunner()
    result = runner.invoke(cli, ["platforms"])
    assert result.exit_code == 0
    assert "Claude Code" in result.output
    assert "Gemini CLI" in result.output


def test_init_installs_selected_platform(tmp_path: Path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["init", "--platform", "claude-code"])
        assert result.exit_code == 0, result.output

        p = get_platform("claude-code")
        skill_md = Path.cwd() / p.skills_path / "inferspec-scan" / "SKILL.md"
        config = Path.cwd() / p.config_file
        assert skill_md.exists()
        assert START_MARKER in config.read_text()


def test_init_writes_config_file(tmp_path: Path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init", "--platform", "claude-code"])
        cfg = Path.cwd() / ".inferspec.yaml"
        assert cfg.exists()
        assert "platforms:" in cfg.read_text()
        assert "claude-code" in cfg.read_text()


def test_uninstall_removes_skills_and_block(tmp_path: Path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init", "--platform", "claude-code"])
        result = runner.invoke(cli, ["uninstall", "--yes"])
        assert result.exit_code == 0, result.output

        p = get_platform("claude-code")
        assert not (Path.cwd() / p.skills_path / "inferspec-scan").exists()
        config = Path.cwd() / p.config_file
        if config.exists():
            assert START_MARKER not in config.read_text()


def test_doctor_reports_status(tmp_path: Path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init", "--platform", "claude-code"])
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "claude-code" in result.output.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'inferspec.cli'`

- [ ] **Step 3: Write the implementation**

`src/inferspec/cli.py`:
```python
import shutil
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

from inferspec.installer import install_platform
from inferspec.managed_block import START_MARKER, END_MARKER
from inferspec.platforms import PLATFORMS, get_platform, get_platforms_by_ids

console = Console()
CONFIG_FILE = ".inferspec.yaml"


def _load_config() -> dict | None:
    path = Path.cwd() / CONFIG_FILE
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text()) or {}


def _save_config(cfg: dict) -> None:
    (Path.cwd() / CONFIG_FILE).write_text(yaml.dump(cfg, default_flow_style=False))


@click.group()
def cli():
    """InferSpec — reverse-infer OpenSpec specs from code + context."""


@cli.command()
@click.option(
    "--platform",
    "platforms_opt",
    multiple=True,
    type=click.Choice([p.id for p in PLATFORMS]),
    help="Host CLI to install into. Repeatable. If omitted, prompts interactively.",
)
def init(platforms_opt: tuple[str, ...]):
    """Install InferSpec skills into selected host CLI(s)."""
    if platforms_opt:
        selected = get_platforms_by_ids(list(platforms_opt))
    else:
        console.print("\n[bold cyan]🔍 InferSpec — Initialize[/bold cyan]\n")
        table = Table(show_header=False)
        for i, p in enumerate(PLATFORMS, 1):
            table.add_row(str(i), p.name)
        console.print(table)
        raw = click.prompt("\nSelect platforms (comma-separated numbers)", type=str)
        indices = [int(x.strip()) - 1 for x in raw.split(",") if x.strip().isdigit()]
        selected = [PLATFORMS[i] for i in indices if 0 <= i < len(PLATFORMS)]

    if not selected:
        console.print("[red]No valid platforms selected.[/red]")
        raise SystemExit(1)

    project_dir = Path.cwd()
    for p in selected:
        install_platform(project_dir, p)
        console.print(f"  [green]✅[/green] Installed to {p.skills_path}")

    _save_config({"platforms": [p.id for p in selected]})
    console.print(f"\n[green]✅[/green] Config saved to {CONFIG_FILE}")
    console.print("\n[bold]Done. Open your AI agent and run /inferspec-scan in a repo.[/bold]\n")


@cli.command()
def platforms():
    """List all supported host platforms."""
    table = Table(title="Supported Platforms")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Skills Path")
    table.add_column("Config File")
    for p in PLATFORMS:
        table.add_row(p.id, p.name, p.skills_path, p.config_file)
    console.print(table)


@cli.command()
def doctor():
    """Report install status in the current directory."""
    cfg = _load_config()
    if cfg is None:
        console.print("[yellow]No .inferspec.yaml in this directory. Run `inferspec init`.[/yellow]")
        return

    project_dir = Path.cwd()
    for pid in cfg.get("platforms", []):
        p = get_platform(pid)
        if p is None:
            console.print(f"  [red]✗[/red] {pid}: unknown platform id")
            continue
        skill = project_dir / p.skills_path / "inferspec-scan" / "SKILL.md"
        config = project_dir / p.config_file
        skill_ok = skill.exists()
        block_ok = config.exists() and START_MARKER in config.read_text()
        mark = "[green]✓[/green]" if skill_ok and block_ok else "[red]✗[/red]"
        console.print(f"  {mark} {p.name}: skill={skill_ok} block={block_ok}")


@cli.command()
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def uninstall(yes: bool):
    """Remove InferSpec skills and managed blocks from this directory."""
    cfg = _load_config()
    if cfg is None:
        console.print("[yellow]Nothing to uninstall (no .inferspec.yaml).[/yellow]")
        return

    if not yes and not click.confirm("Remove InferSpec skills from this directory?"):
        return

    project_dir = Path.cwd()
    for pid in cfg.get("platforms", []):
        p = get_platform(pid)
        if p is None:
            continue
        skill_dir = project_dir / p.skills_path / "inferspec-scan"
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
        config = project_dir / p.config_file
        if config.exists():
            text = config.read_text()
            import re
            pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER) + r"\n?", re.DOTALL)
            new_text = pattern.sub("", text).rstrip() + "\n"
            config.write_text(new_text)
        console.print(f"  [green]✅[/green] Removed from {p.name}")

    cfg_path = project_dir / CONFIG_FILE
    if cfg_path.exists():
        cfg_path.unlink()
    console.print("\n[bold]Uninstall complete.[/bold]\n")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: 5 passed

- [ ] **Step 5: Smoke-test the actual CLI**

Run:
```bash
cd /tmp && rm -rf inferspec-smoke && mkdir inferspec-smoke && cd inferspec-smoke
inferspec platforms
inferspec init --platform claude-code
ls .claude/skills/inferspec-scan/
inferspec doctor
inferspec uninstall --yes
```

Expected: each command exits 0; after init the skill file exists; after uninstall it's gone.

- [ ] **Step 6: Commit**

```bash
git add src/inferspec/cli.py tests/test_cli.py
git commit -m "feat: inferspec CLI (init/platforms/doctor/uninstall)"
```

---

## Task 6: Full `/inferspec-scan` SKILL.md (the actual reasoning logic)

**Files:**
- Modify: `src/inferspec/skills/inferspec-scan/SKILL.md` (replace stub with full content)
- Create: `src/inferspec/skills/inferspec-scan/spec_template.md`
- Create: `src/inferspec/skills/inferspec-scan/prompts/classify_capabilities.md`
- Create: `src/inferspec/skills/inferspec-scan/prompts/draft_spec.md`

- [ ] **Step 1: Write `spec_template.md` — the OpenSpec skeleton**

`src/inferspec/skills/inferspec-scan/spec_template.md`:
```markdown
## Purpose

{purpose_paragraph_or_tbd}

## Requirements

{requirements_blocks}

<!-- __inferspec_meta__: {{"hash": "{hash}", "scan_ts": "{timestamp}", "version": "0.1"}} -->
```

(Curly-brace placeholders are filled by the skill at draft time — they're not Python f-strings, just string replace targets.)

- [ ] **Step 2: Write `classify_capabilities.md`**

`src/inferspec/skills/inferspec-scan/prompts/classify_capabilities.md`:
```markdown
You are grouping files into product capabilities for spec inference.

INPUT:
- `graphify-out/graph.json` — AST + import graph for this repo
- `graphify-out/features.json` (if exists) — previous capability list

TASK:
1. Read graph.json. Identify clusters of files that serve one product capability.
2. Treat low-level utilities (`utils`, `common`, `config`, `logger`, telemetry) as
   "infrastructure" and SKIP them — they don't get specs.
3. Always include OpenAPI/Swagger spec files as their own capabilities
   (search `doc/`, `docs/`, `api/`, `openapi/`, `spec/`, `specs/` for files with
   `openapi:`, `swagger:`, or top-level `paths:` keys).
4. Output to `graphify-out/features.json`:
   ```json
   [
     {"name": "user-auth", "files": ["src/auth.py", "src/login.py"]},
     {"name": "order-mgmt", "files": ["src/order.py", "pages/order.vue"]}
   ]
   ```

Naming rules:
- kebab-case
- describe the capability, not the technology (`user-auth` not `auth-py`)
- 2-4 words

If features.json already exists, prefer keeping existing capability names so
hash-skip works across runs.
```

- [ ] **Step 3: Write `draft_spec.md`**

`src/inferspec/skills/inferspec-scan/prompts/draft_spec.md`:
```markdown
You are drafting an OpenSpec `spec.md` for ONE capability.

INPUT (provided in context):
- `cap.name` — kebab-case capability slug
- `cap.files` — source files in this capability
- File contents (read them with the Read tool)
- Git log for these files (provided via `git log` output)
- Matched docs from `docs/`, `README.md`, `CHANGELOG.md`, existing `openspec/`
- (Optional) Jira/Confluence MCP results if available
- (Optional) URLs the user pasted (fetched via host's WebFetch tool)

OUTPUT FORMAT — strict OpenSpec:

```markdown
## Purpose

<1-2 paragraphs of PM-intent. Prefer phrasing from:
 1. Commit messages that introduced the feature
 2. PR descriptions
 3. Jira tickets
 4. README sections that reference the cap
If none of these reveal intent, write `<!-- [TBD: Purpose] -->`.>

## Requirements

### Requirement: <Short Name>
The system SHALL/MUST/SHOULD <observable behaviour>.

**Source:** <file:line>[, <file:line>...][, <ticket-id>]

#### Scenario: <Specific case>
- **GIVEN** <precondition>
- **WHEN** <trigger>
- **THEN** <observable outcome>

<!-- Mark inferred-but-unverified values with [GAP] inside an HTML comment
     at end of the affected scenario line, e.g.:
     - **THEN** server returns 429  <!-- [GAP: rate limit value inferred] -->
-->

### Requirement: ...
...
```

RULES:
- Use RFC 2119 keywords MUST / SHALL / SHOULD / MAY.
- Every Requirement gets a `**Source:**` line citing file:line and/or ticket IDs.
- Mark ambiguity with `<!-- [GAP: <reason>] -->`. Don't invent values.
- One Scenario per distinct case (GIVEN/WHEN/THEN form).
- Don't repeat code in the spec — describe behaviour observable from outside.
- Don't write Requirements for purely internal helpers — those belong to whatever
  external-facing Requirement uses them.
```

- [ ] **Step 4: Write the full SKILL.md (replace stub)**

`src/inferspec/skills/inferspec-scan/SKILL.md`:
```markdown
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
```

- [ ] **Step 5: Verify package install picks up the new files**

The hatch `force-include` config from Task 1 already includes `src/inferspec/skills`. Reinstall and confirm:

Run:
```bash
.venv/bin/pip install -e ".[dev]" -q 2>&1 | tail -3
python3 -c "import importlib.resources; print(list((importlib.resources.files('inferspec') / 'skills' / 'inferspec-scan').iterdir()))"
```
Expected: lists `SKILL.md`, `spec_template.md`, `prompts/`

- [ ] **Step 6: Add a test that the SKILL.md is structurally valid**

Append to `tests/test_installer.py`:
```python
def test_installed_skill_has_required_files(tmp_path: Path):
    p = get_platform("claude-code")
    install_platform(tmp_path, p)
    skill_root = tmp_path / p.skills_path / "inferspec-scan"
    assert (skill_root / "SKILL.md").exists()
    assert (skill_root / "spec_template.md").exists()
    assert (skill_root / "prompts" / "classify_capabilities.md").exists()
    assert (skill_root / "prompts" / "draft_spec.md").exists()

    skill_text = (skill_root / "SKILL.md").read_text()
    assert "name: inferspec-scan" in skill_text
    assert "OpenSpec" in skill_text
    assert "graphify" in skill_text
```

Run: `pytest tests/test_installer.py::test_installed_skill_has_required_files -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/inferspec/skills/inferspec-scan/ tests/test_installer.py
git commit -m "feat: full /inferspec-scan skill with OpenSpec drafting prompts"
```

---

## Task 7: Demo target — `examples/legacy-flask-app/`

**Files:**
- Create: `examples/legacy-flask-app/README.md`
- Create: `examples/legacy-flask-app/app.py`
- Create: `examples/legacy-flask-app/auth.py`
- Create: `examples/legacy-flask-app/orders.py`

- [ ] **Step 1: Write the demo Flask app**

`examples/legacy-flask-app/README.md`:
```markdown
# Legacy Flask Demo

Tiny Flask app used as InferSpec's reference target. Three "capabilities":
authentication, orders, and a health check.

Run `/inferspec-scan` here from your AI agent to produce specs at
`openspec/specs/*/spec.md`.
```

`examples/legacy-flask-app/app.py`:
```python
from flask import Flask, jsonify
from auth import bp as auth_bp
from orders import bp as orders_bp

app = Flask(__name__)
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(orders_bp, url_prefix="/orders")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000)
```

`examples/legacy-flask-app/auth.py`:
```python
from collections import defaultdict
from time import time

from flask import Blueprint, jsonify, request

bp = Blueprint("auth", __name__)

_USERS = {"alice": "secret123", "bob": "hunter2"}
_FAILED_ATTEMPTS: dict[str, list[float]] = defaultdict(list)


def _rate_limited(user: str) -> bool:
    now = time()
    _FAILED_ATTEMPTS[user] = [t for t in _FAILED_ATTEMPTS[user] if now - t < 60]
    return len(_FAILED_ATTEMPTS[user]) >= 5


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = data.get("user", "")
    pw = data.get("password", "")

    if _rate_limited(user):
        return jsonify({"error": "too many attempts"}), 429

    if _USERS.get(user) != pw:
        _FAILED_ATTEMPTS[user].append(time())
        return jsonify({"error": "bad credentials"}), 401

    return jsonify({"token": f"session-{user}"}), 200
```

`examples/legacy-flask-app/orders.py`:
```python
from flask import Blueprint, jsonify, request

bp = Blueprint("orders", __name__)
_ORDERS: dict[int, dict] = {}
_NEXT_ID = 1


@bp.route("", methods=["POST"])
def create_order():
    global _NEXT_ID
    data = request.get_json() or {}
    if "item" not in data:
        return jsonify({"error": "item required"}), 400
    order = {"id": _NEXT_ID, "item": data["item"], "status": "pending"}
    _ORDERS[_NEXT_ID] = order
    _NEXT_ID += 1
    return jsonify(order), 201


@bp.route("/<int:order_id>", methods=["GET"])
def get_order(order_id: int):
    o = _ORDERS.get(order_id)
    if o is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(o)
```

- [ ] **Step 2: Verify it imports cleanly**

Run:
```bash
cd examples/legacy-flask-app && python3 -c "import app; print('ok')" 2>&1 | tail -3
cd ../..
```
Expected: prints `ok`. If `flask` isn't installed, that's fine — we don't need to run it, just confirm the source is syntactically valid Python.

Actually run a syntax check instead:
```bash
python3 -m py_compile examples/legacy-flask-app/app.py examples/legacy-flask-app/auth.py examples/legacy-flask-app/orders.py
echo "syntax ok"
```
Expected: `syntax ok`

- [ ] **Step 3: Commit**

```bash
git add examples/
git commit -m "examples: add legacy-flask-app demo target"
```

---

## Task 8: End-to-end installer smoke test against the demo

**Files:**
- Create: `tests/test_e2e_install.py`

This test doesn't exercise the LLM (we can't from CI), but it does verify the whole installer chain copies a usable skill into a fresh checkout of `examples/legacy-flask-app`.

- [ ] **Step 1: Write the test**

`tests/test_e2e_install.py`:
```python
import shutil
from pathlib import Path

import pytest

from inferspec.installer import install_platform
from inferspec.platforms import get_platform


@pytest.fixture
def flask_demo_copy(tmp_path: Path) -> Path:
    src = Path(__file__).resolve().parent.parent / "examples" / "legacy-flask-app"
    dst = tmp_path / "legacy-flask-app"
    shutil.copytree(src, dst)
    return dst


def test_install_into_flask_demo(flask_demo_copy: Path):
    p = get_platform("claude-code")
    install_platform(flask_demo_copy, p)

    skill = flask_demo_copy / p.skills_path / "inferspec-scan" / "SKILL.md"
    spec_template = flask_demo_copy / p.skills_path / "inferspec-scan" / "spec_template.md"
    classify_prompt = flask_demo_copy / p.skills_path / "inferspec-scan" / "prompts" / "classify_capabilities.md"
    draft_prompt = flask_demo_copy / p.skills_path / "inferspec-scan" / "prompts" / "draft_spec.md"
    config = flask_demo_copy / p.config_file

    assert skill.exists()
    assert spec_template.exists()
    assert classify_prompt.exists()
    assert draft_prompt.exists()
    assert config.exists()


def test_skill_references_existing_prompt_files(flask_demo_copy: Path):
    p = get_platform("claude-code")
    install_platform(flask_demo_copy, p)
    skill_text = (
        flask_demo_copy / p.skills_path / "inferspec-scan" / "SKILL.md"
    ).read_text()

    assert "classify_capabilities.md" in skill_text
    assert "draft_spec.md" in skill_text
```

- [ ] **Step 2: Run**

Run: `pytest tests/test_e2e_install.py -v`
Expected: 2 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e_install.py
git commit -m "test: end-to-end installer check against flask demo"
```

---

## Task 9: CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the workflow**

`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install
        run: |
          pip install -e ".[dev]"
      - name: Test
        run: |
          pytest -v
```

- [ ] **Step 2: Verify locally before pushing**

Run: `pytest -v 2>&1 | tail -10`
Expected: all tests pass (counts from previous tasks: ~17 tests)

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add pytest matrix for Python 3.12/3.13"
```

---

## Task 10: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

`README.md`:
```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README for v0.1"
```

---

## Task 11: Final verification

- [ ] **Step 1: Full test suite**

Run: `pytest -v 2>&1 | tail -20`
Expected: every test passes, no warnings about missing files.

- [ ] **Step 2: Lint-check the skill markdown**

Run:
```bash
python3 -c "
import importlib.resources, re
from pathlib import Path

skill = (importlib.resources.files('inferspec') / 'skills' / 'inferspec-scan' / 'SKILL.md').read_text()
# Frontmatter present
assert skill.startswith('---'), 'Missing frontmatter'
# Name field correct
assert re.search(r'^name:\s*inferspec-scan', skill, re.M), 'Bad name'
# Description not empty
m = re.search(r'^description:\s*(.+)$', skill, re.M)
assert m and len(m.group(1).strip()) > 20, 'Description too short'
print('SKILL.md frontmatter OK')
"
```
Expected: `SKILL.md frontmatter OK`

- [ ] **Step 3: Real-world smoke test**

Run:
```bash
TMP=$(mktemp -d)
cp -r examples/legacy-flask-app "$TMP/demo"
cd "$TMP/demo"
inferspec init --platform claude-code
ls .claude/skills/inferspec-scan/
cat .claude/skills/inferspec-scan/SKILL.md | head -20
test -f CLAUDE.md && echo "CLAUDE.md created"
inferspec doctor
inferspec uninstall --yes
cd -
rm -rf "$TMP"
```
Expected: skill files listed, frontmatter visible, CLAUDE.md created, doctor reports OK, uninstall succeeds.

- [ ] **Step 4: Tag the milestone (no PyPI release yet — that's a follow-up plan)**

```bash
git tag v0.1.0-foundation -m "Foundation milestone: /inferspec-scan installable + drafts OpenSpec"
git log --oneline | head -15
```

---

## Self-Review

**Spec coverage check (against `2026-05-20-inferspec-design.md`):**

| Spec section | Implemented by task |
|---|---|
| § 2.1 Two-layer split | Task 1 (Python pkg), Task 6 (Skill md) |
| § 2.2 Repo structure | Task 1, 6, 7 |
| § 2.3 Three skills — `/inferspec-scan` | Task 6 |
| § 2.3 Three skills — `/inferspec-cap`, `/inferspec-refine` | **Out of scope for this plan** (subsequent plan) |
| § 2.4 Pipeline Stage 1 (graphify) | Task 6 SKILL.md Step 1 |
| § 2.4 Pipeline Stage 2 (context collection) | Task 6 SKILL.md Step 3 + 4b |
| § 2.4 Pipeline Stage 3 (LLM drafting) | Task 6 SKILL.md Step 4c, draft_spec.md prompt |
| § 2.4 Pipeline Stage 4 (Q&A) | **Out of scope** (cap/refine skills) |
| § 2.5 MCP detection | Task 6 SKILL.md Step 3 |
| § 3.1 OpenSpec convention | Task 6 (spec_template.md, draft_spec.md) |
| § 3.2 Mode A scan flow | Task 6 SKILL.md |
| § 3.3 Git history usage | Task 6 SKILL.md Step 4b |
| § 3.4 Hash-skip incremental | Task 6 SKILL.md Step 4a |
| § 3.5 Output layout (.inferspec.yaml) | Task 5 CLI |
| § 4.1 MVP — uvx package + 5 platforms | Tasks 3, 5 (registry covers all 5; init defaults to claude-code for v0.1 ship) |
| § 4.1 MVP — `inferspec init/doctor/uninstall` | Task 5 |
| § 4.3 Success criterion 1 (uvx install works) | Task 5, 11 |
| § 4.3 Success criterion 2 (`/inferspec-scan` produces valid OpenSpec) | Task 6, 8 (smoke), 11 |
| § 4.3 Success criterion 3 (Q&A loop) | **Out of scope** (cap skill) |
| § 4.3 Success criterion 4 (MCP detection skips cleanly) | Task 6 SKILL.md Step 3 |
| § 4.3 Success criterion 5 (CI green, README) | Tasks 9, 10 |
| § 4.3 Success criterion 6 (outside testers) | Manual, post-implementation |

**Placeholder scan:** None. Every step has concrete code or commands.

**Type consistency:** `Platform.skills_path` used consistently across `platforms.py`, `installer.py`, `cli.py`, all tests. `START_MARKER`/`END_MARKER` exported from `managed_block.py` and reused everywhere.

**Cross-task naming:** `install_platform` signature consistent. CLI commands `init/platforms/doctor/uninstall` referenced consistently in tests and README.

**Follow-up plans needed (explicitly deferred):**
1. `2026-XX-XX-inferspec-cap.md` — `/inferspec-cap <slug>` interactive skill + Q&A loop
2. `2026-XX-XX-inferspec-refine.md` — `/inferspec-refine` gap-fill skill
3. `2026-XX-XX-inferspec-pypi-release.md` — PyPI publish + multi-platform smoke tests (Gemini/Codex/Copilot)
