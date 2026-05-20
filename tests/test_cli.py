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
        assert not (Path.cwd() / p.skills_path / "inferspec-cap").exists()
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
        # Both skills should be reported
        assert "scan=" in result.output.lower()
        assert "cap=" in result.output.lower()
