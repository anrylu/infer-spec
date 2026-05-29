import importlib.resources
import shutil
from pathlib import Path

from inferspec import __version__
from inferspec.managed_block import write_block
from inferspec.platforms import Platform

VERSION_STAMP = ".inferspec-version"


def _bundled_skills_dir() -> Path:
    return Path(str(importlib.resources.files("inferspec") / "skills"))


def read_installed_version(skill_dir: Path) -> str | None:
    stamp = skill_dir / VERSION_STAMP
    if not stamp.exists():
        return None
    return stamp.read_text().strip() or None


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


def install_platform(project_dir: Path, platform: Platform) -> None:
    skills_root = project_dir / platform.skills_path
    skills_root.mkdir(parents=True, exist_ok=True)

    src_root = _bundled_skills_dir()
    for skill_dir in sorted(p for p in src_root.iterdir() if p.is_dir()):
        dest = skills_root / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        (dest / VERSION_STAMP).write_text(__version__ + "\n")

    config_file = project_dir / platform.config_file
    config_file.parent.mkdir(parents=True, exist_ok=True)
    write_block(config_file, _managed_block_content())
