from pathlib import Path

import pytest
import yaml

from agentsec.config import ConfigError, load_config

REPO_CONFIG = Path(__file__).parents[2] / "config"
ENV = {"OLLAMA_MODEL": "stub-model", "OLLAMA_BASE_URL": "http://ollama.test:11434"}


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    for name in ("models.yaml", "defenses.yaml", "policy.yaml"):
        (tmp_path / name).write_text((REPO_CONFIG / name).read_text())
    return tmp_path


def _edit_defenses(config_dir: Path, edit_key: str, value: object) -> None:
    path = config_dir / "defenses.yaml"
    data = yaml.safe_load(path.read_text())
    data["profiles"]["baseline"][edit_key] = value
    path.write_text(yaml.safe_dump(data))


def test_shipped_config_files_load() -> None:
    config = load_config(REPO_CONFIG, ENV)
    assert config.models.model == "stub-model"
    assert str(config.models.base_url) == "http://ollama.test:11434/"
    assert config.defenses.active_profile == "baseline"
    assert config.policy.tool_allowlists["orchestrator"] == []


def test_baseline_profile_has_every_layer_off() -> None:
    profiles = load_config(REPO_CONFIG, ENV).defenses.profiles
    assert not any(profiles["baseline"].model_dump().values())
    assert all(profiles["all"].model_dump().values())


@pytest.mark.parametrize("env", [{}, {"OLLAMA_MODEL": ""}, {"OLLAMA_MODEL": "  "}])
def test_unset_model_fails_naming_the_variable(config_dir: Path, env: dict[str, str]) -> None:
    with pytest.raises(ConfigError, match="OLLAMA_MODEL is not set"):
        load_config(config_dir, {"OLLAMA_BASE_URL": ENV["OLLAMA_BASE_URL"], **env})


def test_unset_base_url_fails_naming_the_variable(config_dir: Path) -> None:
    with pytest.raises(ConfigError, match="OLLAMA_BASE_URL is not set"):
        load_config(config_dir, {"OLLAMA_MODEL": "stub-model"})


@pytest.mark.parametrize(
    "url", ["file:///etc/passwd", "not a url", "http://user:secret@ollama.test:11434"]
)
def test_unusable_base_url_is_rejected(config_dir: Path, url: str) -> None:
    with pytest.raises(ConfigError, match="base_url"):
        load_config(config_dir, {**ENV, "OLLAMA_BASE_URL": url})


def test_credentials_in_base_url_are_not_echoed_in_the_error(config_dir: Path) -> None:
    url = "http://user:secret@ollama.test:11434"
    with pytest.raises(ConfigError) as caught:
        load_config(config_dir, {**ENV, "OLLAMA_BASE_URL": url})
    assert "secret" not in str(caught.value)


def test_unknown_defense_key_is_rejected(config_dir: Path) -> None:
    _edit_defenses(config_dir, "made_up_layer", False)
    with pytest.raises(ConfigError, match="made_up_layer"):
        load_config(config_dir, ENV)


def test_non_boolean_flag_is_rejected(config_dir: Path) -> None:
    _edit_defenses(config_dir, "sandbox", "no")
    with pytest.raises(ConfigError, match="sandbox"):
        load_config(config_dir, ENV)


def test_hardened_baseline_is_rejected(config_dir: Path) -> None:
    _edit_defenses(config_dir, "sandbox", True)
    with pytest.raises(ConfigError, match="'baseline' must have every layer off"):
        load_config(config_dir, ENV)


def test_missing_profile_is_rejected(config_dir: Path) -> None:
    path = config_dir / "defenses.yaml"
    data = yaml.safe_load(path.read_text())
    del data["profiles"]["all"]
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ConfigError, match="profile 'all' is required"):
        load_config(config_dir, ENV)


def test_active_profile_must_exist(config_dir: Path) -> None:
    path = config_dir / "defenses.yaml"
    data = yaml.safe_load(path.read_text())
    data["active_profile"] = "nonexistent"
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ConfigError, match="nonexistent"):
        load_config(config_dir, ENV)


def test_missing_file_is_reported(config_dir: Path) -> None:
    (config_dir / "policy.yaml").unlink()
    with pytest.raises(ConfigError, match=r"cannot read .*policy\.yaml"):
        load_config(config_dir, ENV)


def test_malformed_yaml_is_reported(config_dir: Path) -> None:
    (config_dir / "policy.yaml").write_text("tool_allowlists: [unclosed")
    with pytest.raises(ConfigError, match="not valid YAML"):
        load_config(config_dir, ENV)
