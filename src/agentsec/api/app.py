"""The FastAPI application: read-only endpoints and the browser UI."""

import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agentsec.config import (
    ConfigError,
    DefensesConfig,
    load_defenses,
    load_models,
    load_repro_settings,
)

SCENARIO_FILE = re.compile(r"^[a-z]+-\d{3}\.yaml$")
SCENARIO_FOLDERS: dict[str, Literal["attack", "benign"]] = {"attacks": "attack", "benign": "benign"}


class Scenario(BaseModel):
    id: str
    kind: Literal["attack", "benign"]


class Results(BaseModel):
    model: str | None
    seed: int
    scenarios: int
    trials_per_scenario: int | None
    attack_success: dict[str, dict[str, float]]
    normal_tasks: dict[str, dict[str, float]]


def list_scenarios(scenario_dir: Path) -> list[Scenario]:
    return [
        Scenario(id=path.stem, kind=kind)
        for folder, kind in SCENARIO_FOLDERS.items()
        for path in sorted((scenario_dir / folder).glob("*.yaml"))
        if SCENARIO_FILE.fullmatch(path.name)
    ]


def _configured_model(config_dir: Path, env: Mapping[str, str]) -> str | None:
    # An unset model is a normal state, not an error, until something needs to call it.
    try:
        return load_models(config_dir, env).model
    except ConfigError:
        return None


def create_app(env: Mapping[str, str] | None = None) -> FastAPI:
    # Config is read per request: /health must work before a model has been chosen.
    settings = os.environ if env is None else env
    config_dir = Path(settings.get("AGENTSEC_CONFIG_DIR", "config"))
    scenario_dir = Path(settings.get("AGENTSEC_SCENARIO_DIR", "scenarios"))
    web_dir = Path(settings.get("AGENTSEC_WEB_DIR", "web"))

    api = FastAPI(title="agentsec", docs_url=None, redoc_url=None, openapi_url=None)

    @api.exception_handler(ConfigError)
    def config_error(_request: Request, _exc: ConfigError) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": "config is invalid; run agentsec check"}
        )

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/config/defenses")
    def defenses() -> DefensesConfig:
        return load_defenses(config_dir)

    @api.get("/scenarios")
    def scenarios() -> list[Scenario]:
        return list_scenarios(scenario_dir)

    @api.get("/results")
    def results() -> Results:
        # The rates stay empty until the harness (milestone 4) produces logs to compute them from.
        return Results(
            model=_configured_model(config_dir, settings),
            seed=load_repro_settings(config_dir).seed,
            scenarios=len(list_scenarios(scenario_dir)),
            trials_per_scenario=None,
            attack_success={},
            normal_tasks={},
        )

    # Mounted last so the API routes above take priority.
    api.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
    return api
