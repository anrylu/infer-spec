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
