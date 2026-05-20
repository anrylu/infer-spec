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


def test_skill_references_existing_prompt_files(flask_demo_copy: Path):
    p = get_platform("claude-code")
    install_platform(flask_demo_copy, p)
    skill_text = (
        flask_demo_copy / p.skills_path / "inferspec-scan" / "SKILL.md"
    ).read_text()

    assert "classify_capabilities.md" in skill_text
    assert "draft_spec.md" in skill_text
