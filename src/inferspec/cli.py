import shutil
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

from inferspec.installer import install_platform
from inferspec.managed_block import START_MARKER, END_MARKER
from inferspec.platforms import PLATFORMS, get_platform, get_platforms_by_ids

console = Console()
CONFIG_FILE = ".inferspec.yaml"


def _load_config() -> dict | None:
    path = Path.cwd() / CONFIG_FILE
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text()) or {}


def _save_config(cfg: dict) -> None:
    (Path.cwd() / CONFIG_FILE).write_text(yaml.dump(cfg, default_flow_style=False))


@click.group()
def cli():
    """InferSpec — reverse-infer OpenSpec specs from code + context."""


@cli.command()
@click.option(
    "--platform",
    "platforms_opt",
    multiple=True,
    type=click.Choice([p.id for p in PLATFORMS]),
    help="Host CLI to install into. Repeatable. If omitted, prompts interactively.",
)
def init(platforms_opt: tuple[str, ...]):
    """Install InferSpec skills into selected host CLI(s)."""
    if platforms_opt:
        selected = get_platforms_by_ids(list(platforms_opt))
    else:
        console.print("\n[bold cyan]🔍 InferSpec — Initialize[/bold cyan]\n")
        table = Table(show_header=False)
        for i, p in enumerate(PLATFORMS, 1):
            table.add_row(str(i), p.name)
        console.print(table)
        raw = click.prompt("\nSelect platforms (comma-separated numbers)", type=str)
        indices = [int(x.strip()) - 1 for x in raw.split(",") if x.strip().isdigit()]
        selected = [PLATFORMS[i] for i in indices if 0 <= i < len(PLATFORMS)]

    if not selected:
        console.print("[red]No valid platforms selected.[/red]")
        raise SystemExit(1)

    project_dir = Path.cwd()
    for p in selected:
        install_platform(project_dir, p)
        console.print(f"  [green]✅[/green] Installed to {p.skills_path}")

    _save_config({"platforms": [p.id for p in selected]})
    console.print(f"\n[green]✅[/green] Config saved to {CONFIG_FILE}")
    console.print("\n[bold]Done. Open your AI agent and run /inferspec-scan in a repo.[/bold]\n")


@cli.command()
def platforms():
    """List all supported host platforms."""
    table = Table(title="Supported Platforms")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Skills Path")
    table.add_column("Config File")
    for p in PLATFORMS:
        table.add_row(p.id, p.name, p.skills_path, p.config_file)
    console.print(table)


@cli.command()
def doctor():
    """Report install status in the current directory."""
    cfg = _load_config()
    if cfg is None:
        console.print("[yellow]No .inferspec.yaml in this directory. Run `inferspec init`.[/yellow]")
        return

    project_dir = Path.cwd()
    for pid in cfg.get("platforms", []):
        p = get_platform(pid)
        if p is None:
            console.print(f"  [red]✗[/red] {pid}: unknown platform id")
            continue
        skill = project_dir / p.skills_path / "inferspec-scan" / "SKILL.md"
        config = project_dir / p.config_file
        skill_ok = skill.exists()
        block_ok = config.exists() and START_MARKER in config.read_text()
        mark = "[green]✓[/green]" if skill_ok and block_ok else "[red]✗[/red]"
        console.print(f"  {mark} {p.name} ({p.id}): skill={skill_ok} block={block_ok}")


@cli.command()
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def uninstall(yes: bool):
    """Remove InferSpec skills and managed blocks from this directory."""
    cfg = _load_config()
    if cfg is None:
        console.print("[yellow]Nothing to uninstall (no .inferspec.yaml).[/yellow]")
        return

    if not yes and not click.confirm("Remove InferSpec skills from this directory?"):
        return

    project_dir = Path.cwd()
    for pid in cfg.get("platforms", []):
        p = get_platform(pid)
        if p is None:
            continue
        skill_dir = project_dir / p.skills_path / "inferspec-scan"
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
        config = project_dir / p.config_file
        if config.exists():
            text = config.read_text()
            import re
            pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER) + r"\n?", re.DOTALL)
            new_text = pattern.sub("", text).rstrip() + "\n"
            config.write_text(new_text)
        console.print(f"  [green]✅[/green] Removed from {p.name}")

    cfg_path = project_dir / CONFIG_FILE
    if cfg_path.exists():
        cfg_path.unlink()
    console.print("\n[bold]Uninstall complete.[/bold]\n")


if __name__ == "__main__":
    cli()
