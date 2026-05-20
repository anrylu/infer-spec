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
