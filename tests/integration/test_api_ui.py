from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agentsec.api.app import create_app

REPO = Path(__file__).parents[2]


@pytest.fixture
def scenario_dir(tmp_path: Path) -> Path:
    (tmp_path / "attacks").mkdir()
    (tmp_path / "benign").mkdir()
    return tmp_path


def _client(scenario_dir: Path, **env: str) -> TestClient:
    settings = {
        "AGENTSEC_CONFIG_DIR": str(REPO / "config"),
        "AGENTSEC_WEB_DIR": str(REPO / "web"),
        "AGENTSEC_SCENARIO_DIR": str(scenario_dir),
        **env,
    }
    return TestClient(create_app(settings), raise_server_exceptions=False)


def test_defenses_endpoint_returns_the_config_profiles(scenario_dir: Path) -> None:
    body = _client(scenario_dir).get("/config/defenses").json()
    assert body["active_profile"] == "baseline"
    assert not any(body["profiles"]["baseline"].values())
    assert all(body["profiles"]["all"].values())


def test_invalid_config_returns_503_without_leaking_paths(
    scenario_dir: Path, tmp_path: Path
) -> None:
    client = _client(scenario_dir, AGENTSEC_CONFIG_DIR=str(tmp_path / "missing"))
    response = client.get("/config/defenses")
    assert response.status_code == 503
    assert str(tmp_path) not in response.text


def test_scenarios_endpoint_is_empty_without_scenario_files(scenario_dir: Path) -> None:
    assert _client(scenario_dir).get("/scenarios").json() == []


def test_scenarios_endpoint_lists_only_correctly_named_files(scenario_dir: Path) -> None:
    (scenario_dir / "attacks" / "inj-001.yaml").touch()
    (scenario_dir / "attacks" / "notes.yaml").touch()
    (scenario_dir / "benign" / "ben-001.yaml").touch()
    assert _client(scenario_dir).get("/scenarios").json() == [
        {"id": "inj-001", "kind": "attack"},
        {"id": "ben-001", "kind": "benign"},
    ]


def test_results_report_no_rates_before_any_run(scenario_dir: Path) -> None:
    assert _client(scenario_dir).get("/results").json() == {
        "model": None,
        "seed": 491,
        "scenarios": 0,
        "trials_per_scenario": None,
        "attack_success": {},
        "normal_tasks": {},
    }


def test_results_show_the_configured_model(scenario_dir: Path) -> None:
    client = _client(
        scenario_dir, OLLAMA_MODEL="stub-model", OLLAMA_BASE_URL="http://ollama.test:11434"
    )
    assert client.get("/results").json()["model"] == "stub-model"


@pytest.mark.parametrize(
    ("path", "marker"),
    [
        ("/", "Run console"),
        ("/results.html", "attack success rate"),
        ("/console.js", "EventSource"),
        ("/style.css", "#101010"),
    ],
)
def test_ui_files_are_served(scenario_dir: Path, path: str, marker: str) -> None:
    response = _client(scenario_dir).get(path)
    assert response.status_code == 200
    assert marker in response.text


@pytest.mark.parametrize(
    "path", ["/..%2fpyproject.toml", "/%2e%2e/pyproject.toml", "/../config/models.yaml"]
)
def test_static_files_cannot_escape_the_web_directory(scenario_dir: Path, path: str) -> None:
    assert _client(scenario_dir).get(path).status_code == 404


def test_ui_never_builds_markup_from_api_data() -> None:
    for script in (REPO / "web").glob("*.js"):
        text = script.read_text()
        assert "innerHTML" not in text, script
        assert "insertAdjacentHTML" not in text, script
