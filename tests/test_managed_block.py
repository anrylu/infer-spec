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
