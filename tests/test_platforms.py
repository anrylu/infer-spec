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
