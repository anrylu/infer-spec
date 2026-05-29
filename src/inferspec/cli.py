import shutil
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

from inferspec import __version__
from inferspec.installer import install_platform, read_installed_version
from inferspec.managed_block import START_MARKER, END_MARKER
from inferspec.platforms import PLATFORMS, get_platform, get_platforms_by_ids

SKILL_NAMES = ("inferspec-scan", "inferspec-cap")

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
    stale = False
    for pid in cfg.get("platforms", []):
        p = get_platform(pid)
        if p is None:
            console.print(f"  [red]✗[/red] {pid}: unknown platform id")
            continue
        skill_root = project_dir / p.skills_path
        scan_ok = (skill_root / "inferspec-scan" / "SKILL.md").exists()
        cap_ok = (skill_root / "inferspec-cap" / "SKILL.md").exists()
        config = project_dir / p.config_file
        block_ok = config.exists() and START_MARKER in config.read_text()

        versions = {n: read_installed_version(skill_root / n) for n in SKILL_NAMES}
        drift = [n for n, v in versions.items() if v and v != __version__]
        if drift:
            stale = True
        all_ok = scan_ok and cap_ok and block_ok and not drift
        mark = "[green]✓[/green]" if all_ok else "[red]✗[/red]"

        ver_parts = []
        for n in SKILL_NAMES:
            v = versions[n] or "?"
            tag = "[yellow]stale[/yellow]" if v != __version__ and v != "?" else ""
            ver_parts.append(f"{n.split('-')[1]}={v}{(' ' + tag) if tag else ''}")
        console.print(
            f"  {mark} {p.name} ({p.id}): {' '.join(ver_parts)} block={block_ok}"
        )

    console.print(f"\n  package: [cyan]inferspec v{__version__}[/cyan]")
    if stale:
        console.print("  [yellow]⚠ Skill bundles are out of date. Run `inferspec update`.[/yellow]")


@cli.command()
@click.option("--check", is_flag=True, help="Report drift without writing anything.")
def update(check: bool):
    """Refresh installed skill bundles to match the current package version."""
    cfg = _load_config()
    if cfg is None:
        console.print("[yellow]No .inferspec.yaml found. Run `inferspec init` first.[/yellow]")
        raise SystemExit(1)

    project_dir = Path.cwd()
    pids = cfg.get("platforms", [])
    selected = get_platforms_by_ids(pids)
    if not selected:
        console.print("[red]No valid platforms in .inferspec.yaml.[/red]")
        raise SystemExit(1)

    if check:
        drift_found = False
        for p in selected:
            for skill_name in SKILL_NAMES:
                installed = read_installed_version(project_dir / p.skills_path / skill_name)
                state = installed or "missing"
                if state != __version__:
                    drift_found = True
                    console.print(
                        f"  [yellow]⚠[/yellow] {p.name} / {skill_name}: {state} → {__version__}"
                    )
                else:
                    console.print(f"  [green]✓[/green] {p.name} / {skill_name}: {installed}")
        if drift_found:
            console.print("\n[yellow]Run `inferspec update` to apply.[/yellow]")
            raise SystemExit(1)
        console.print(f"\n[green]✅[/green] All bundles match package v{__version__}.")
        return

    for p in selected:
        install_platform(project_dir, p)
        console.print(f"  [green]✅[/green] {p.name} → v{__version__}")
    console.print(f"\n[green]✅[/green] Updated {len(selected)} platform(s) to v{__version__}.\n")


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
        for skill_name in SKILL_NAMES:
            skill_dir = project_dir / p.skills_path / skill_name
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
