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
