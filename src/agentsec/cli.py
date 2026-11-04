"""The `agentsec` command line."""

import http.client
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel
from rich.console import Console
from rich.markup import escape

from agentsec.config import (
    ConfigError,
    load_defenses,
    load_models,
    load_ollama_endpoint,
    load_policy,
)

OLLAMA_PROBE_TIMEOUT_SECONDS = 5

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Agentic AI security lab.")

ConfigDir = Annotated[
    Path,
    typer.Option(envvar="AGENTSEC_CONFIG_DIR", help="Directory holding the config YAML files."),
]


@app.callback()
def _root() -> None:
    # An explicit callback keeps `check` a subcommand; Typer collapses a lone command otherwise.
    pass


def probe_ollama(base_url: str) -> str | None:
    """Return the problem reaching Ollama, or None if it answered."""
    url = f"{base_url.rstrip('/')}/api/version"
    try:
        # The scheme is safe: callers pass a URL validated as http(s) by OllamaEndpoint.
        with urllib.request.urlopen(url, timeout=OLLAMA_PROBE_TIMEOUT_SECONDS):  # noqa: S310
            return None
    except (OSError, http.client.HTTPException) as exc:
        return str(exc)


def _show_section(console: Console, title: str, load: Callable[[], BaseModel]) -> bool:
    """Print one config section. Return False if it failed to load."""
    try:
        section = load()
    except ConfigError as exc:
        console.print(f"[red]{title}: config error:[/red] {escape(str(exc))}")
        return False
    console.print(f"{title}:", style="bold", markup=False)
    console.print(section.model_dump_json(indent=2), markup=False, highlight=False)
    return True


def _show_ollama_status(console: Console, config_dir: Path) -> bool:
    """Print whether Ollama answers. Return False if it does not or its URL is unusable."""
    try:
        base_url = str(load_ollama_endpoint(config_dir, os.environ).base_url)
    except ConfigError as exc:
        console.print(f"[red]ollama: unknown:[/red] {escape(str(exc))}")
        return False
    problem = probe_ollama(base_url)
    if problem is not None:
        console.print(f"[red]ollama: unreachable[/red] at {escape(base_url)} ({escape(problem)})")
        return False
    console.print(f"[green]ollama: reachable[/green] at {escape(base_url)}")
    return True


@app.command()
def check(config_dir: ConfigDir = Path("config")) -> None:
    """Print the loaded config and report whether Ollama is reachable."""
    console = Console(soft_wrap=True)
    results = [
        _show_section(console, "defenses", lambda: load_defenses(config_dir)),
        _show_section(console, "policy", lambda: load_policy(config_dir)),
        _show_section(console, "models", lambda: load_models(config_dir, os.environ)),
        _show_ollama_status(console, config_dir),
    ]
    if not all(results):
        raise typer.Exit(code=1)
