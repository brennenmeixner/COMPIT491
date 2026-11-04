"""Load and validate config/models.yaml, config/defenses.yaml and config/policy.yaml."""

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Self, TypeVar

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StrictBool,
    ValidationError,
    field_validator,
    model_validator,
)

ENV_REFERENCE = re.compile(r"^\$\{([A-Z][A-Z0-9_]*)\}$")
ModelT = TypeVar("ModelT", bound=BaseModel)


class ConfigError(Exception):
    """A config file is missing or invalid, or a variable it needs is unset."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class OllamaEndpoint(_Strict):
    base_url: HttpUrl

    @field_validator("base_url")
    @classmethod
    def _reject_credentials(cls, value: HttpUrl) -> HttpUrl:
        # The URL is printed by `agentsec check`, and secrets must never be printed.
        if value.username or value.password:
            raise ValueError("base_url must not contain credentials")
        return value


class ReproSettings(_Strict):
    temperature: float = Field(ge=0.0)
    seed: int


class ModelsConfig(OllamaEndpoint, ReproSettings):
    model: str = Field(min_length=1)


class DefenseFlags(_Strict):
    input_validation: StrictBool
    output_validation: StrictBool
    tool_permissions: StrictBool
    memory_controls: StrictBool
    sandbox: StrictBool


class DefensesConfig(_Strict):
    active_profile: str
    profiles: dict[str, DefenseFlags]

    @model_validator(mode="after")
    def _check_profiles(self) -> Self:
        for name, expected in (("baseline", False), ("all", True)):
            profile = self.profiles.get(name)
            if profile is None:
                raise ValueError(f"profile '{name}' is required")
            if any(flag is not expected for flag in profile.model_dump().values()):
                state = "on" if expected else "off"
                raise ValueError(f"profile '{name}' must have every layer {state}")
        if self.active_profile not in self.profiles:
            raise ValueError(f"active_profile '{self.active_profile}' is not a defined profile")
        return self

    @property
    def active(self) -> DefenseFlags:
        return self.profiles[self.active_profile]


class CallCaps(_Strict):
    per_run: int = Field(ge=0)
    per_tool: int = Field(ge=0)


class PathRoots(_Strict):
    read: list[str]
    write: list[str]


class PolicyConfig(_Strict):
    tool_allowlists: dict[str, list[str]]
    path_roots: PathRoots
    recipient_allowlist: list[str]
    call_caps: CallCaps


class AppConfig(_Strict):
    models: ModelsConfig
    defenses: DefensesConfig
    policy: PolicyConfig


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc.strerror}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ConfigError(f"{path} must contain a YAML mapping")
    return loaded


def _validate(model: type[ModelT], data: dict[str, Any], path: Path) -> ModelT:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in error['loc']) or '(file)'}: {error['msg']}"
            for error in exc.errors()
        )
        raise ConfigError(f"{path} is invalid: {problems}") from exc


def _resolve_env_references(
    data: dict[str, Any], env: Mapping[str, str], path: Path
) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, value in data.items():
        match = ENV_REFERENCE.match(value) if isinstance(value, str) else None
        if match is None:
            resolved[key] = value
            continue
        name = match.group(1)
        if not env.get(name, "").strip():
            raise ConfigError(
                f"environment variable {name} is not set (required by {path}, key '{key}'). "
                f"Set it in your shell or in .env; see .env.example."
            )
        resolved[key] = env[name]
    return resolved


def load_models(config_dir: Path, env: Mapping[str, str]) -> ModelsConfig:
    path = config_dir / "models.yaml"
    return _validate(ModelsConfig, _resolve_env_references(_read_yaml(path), env, path), path)


def load_ollama_endpoint(config_dir: Path, env: Mapping[str, str]) -> OllamaEndpoint:
    """Load only the Ollama URL, so reachability can be checked while the model is unset."""
    path = config_dir / "models.yaml"
    subset = {key: value for key, value in _read_yaml(path).items() if key == "base_url"}
    return _validate(OllamaEndpoint, _resolve_env_references(subset, env, path), path)


def load_repro_settings(config_dir: Path) -> ReproSettings:
    """Load only the seed and temperature, which need no environment variables."""
    path = config_dir / "models.yaml"
    keys = ReproSettings.model_fields
    subset = {key: value for key, value in _read_yaml(path).items() if key in keys}
    return _validate(ReproSettings, subset, path)


def load_defenses(config_dir: Path) -> DefensesConfig:
    path = config_dir / "defenses.yaml"
    return _validate(DefensesConfig, _read_yaml(path), path)


def load_policy(config_dir: Path) -> PolicyConfig:
    path = config_dir / "policy.yaml"
    return _validate(PolicyConfig, _read_yaml(path), path)


def load_config(config_dir: Path, env: Mapping[str, str]) -> AppConfig:
    return AppConfig(
        models=load_models(config_dir, env),
        defenses=load_defenses(config_dir),
        policy=load_policy(config_dir),
    )
