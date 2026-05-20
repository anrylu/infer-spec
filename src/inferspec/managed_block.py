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
