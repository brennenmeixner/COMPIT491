"""The structured JSONL event log. One file per run, one JSON line per event."""

import re
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

RUN_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]*$"


class EventType(StrEnum):
    MODEL_CALL = "model_call"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    DEFENSE = "defense"


class DefenseLayer(StrEnum):
    INPUT_VALIDATION = "input_validation"
    OUTPUT_VALIDATION = "output_validation"
    TOOL_PERMISSIONS = "tool_permissions"
    MEMORY_CONTROLS = "memory_controls"
    SANDBOX = "sandbox"


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str = Field(pattern=RUN_ID_PATTERN)
    scenario_id: str
    trial: int = Field(ge=0)
    timestamp: AwareDatetime
    agent: str
    event_type: EventType
    content: str
    defense: DefenseLayer | None = None

    @model_validator(mode="after")
    def _defense_event_names_its_layer(self) -> Self:
        if self.event_type is EventType.DEFENSE and self.defense is None:
            raise ValueError("a defense event must name the layer that acted")
        return self


def _utc_now() -> datetime:
    return datetime.now(UTC)


class EventLog:
    """Appends events for a single run to `<log_dir>/<run_id>.jsonl`."""

    def __init__(
        self,
        log_dir: Path,
        run_id: str,
        scenario_id: str,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        # The run id becomes a filename, so it must not be able to leave log_dir.
        if not re.fullmatch(RUN_ID_PATTERN, run_id):
            raise ValueError(f"invalid run id: {run_id!r}")
        self._run_id = run_id
        self._scenario_id = scenario_id
        self._clock = clock
        self.path = log_dir / f"{run_id}.jsonl"

    def record(
        self,
        *,
        trial: int,
        agent: str,
        event_type: EventType,
        content: str,
        defense: DefenseLayer | None = None,
    ) -> Event:
        event = Event(
            run_id=self._run_id,
            scenario_id=self._scenario_id,
            trial=trial,
            timestamp=self._clock(),
            agent=agent,
            event_type=event_type,
            content=content,
            defense=defense,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as log_file:
            log_file.write(event.model_dump_json() + "\n")
        return event
