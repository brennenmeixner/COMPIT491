from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentsec import cli

REPO_CONFIG = Path(__file__).parents[2] / "config"
URL = "http://ollama.test:11434"


def _check(env: dict[str, str | None]) -> tuple[int, str]:
    args = ["check", "--config-dir", str(REPO_CONFIG)]
    result = CliRunner().invoke(cli.app, args, env=env)
    return result.exit_code, result.output


def test_help_lists_the_check_command() -> None:
    result = CliRunner().invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "check" in result.output


def test_check_prints_config_and_reachable_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "probe_ollama", lambda _url: None)
    code, output = _check({"OLLAMA_MODEL": "stub-model", "OLLAMA_BASE_URL": URL})
    assert code == 0
    assert "stub-model" in output
    assert "input_validation" in output
    assert "tool_allowlists" in output
    assert "ollama: reachable" in output


def test_check_fails_when_ollama_is_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "probe_ollama", lambda _url: "connection refused")
    code, output = _check({"OLLAMA_MODEL": "stub-model", "OLLAMA_BASE_URL": URL})
    assert code == 1
    assert "ollama: unreachable" in output
    assert "connection refused" in output


def test_check_fails_clearly_when_model_is_unset_but_still_probes_ollama(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "probe_ollama", lambda _url: None)
    code, output = _check({"OLLAMA_MODEL": None, "OLLAMA_BASE_URL": URL})
    assert code == 1
    assert "environment variable OLLAMA_MODEL is not set" in output
    assert "ollama: reachable" in output


def test_check_never_probes_a_rejected_url(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(_url: str) -> None:
        pytest.fail("probe_ollama was called with a rejected URL")

    monkeypatch.setattr(cli, "probe_ollama", fail_if_called)
    code, output = _check({"OLLAMA_MODEL": "stub-model", "OLLAMA_BASE_URL": "file:///etc/passwd"})
    assert code == 1
    assert "ollama: unknown" in output


def test_probe_reports_a_failed_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_args: object, **_kwargs: object) -> None:
        raise ConnectionRefusedError("connection refused")

    monkeypatch.setattr(cli.urllib.request, "urlopen", refuse)
    assert cli.probe_ollama(URL) == "connection refused"
