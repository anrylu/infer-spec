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
