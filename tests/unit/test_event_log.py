import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from agentsec.event_log import DefenseLayer, Event, EventLog, EventType

FIXED_TIME = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def _log(log_dir: Path, run_id: str = "run-1") -> EventLog:
    return EventLog(log_dir, run_id, scenario_id="inj-001", clock=lambda: FIXED_TIME)


def _lines(log: EventLog) -> list[dict[str, object]]:
    return [json.loads(line) for line in log.path.read_text().splitlines()]


def test_record_writes_one_json_line_with_every_field(tmp_path: Path) -> None:
    log = _log(tmp_path)
    log.record(trial=3, agent="document_agent", event_type=EventType.TOOL_CALL, content="read_file")
    assert _lines(log) == [
        {
            "run_id": "run-1",
            "scenario_id": "inj-001",
            "trial": 3,
            "timestamp": "2026-01-02T03:04:05Z",
            "agent": "document_agent",
            "event_type": "tool_call",
            "content": "read_file",
            "defense": None,
        }
    ]


def test_record_appends_to_the_existing_file(tmp_path: Path) -> None:
    for trial in range(2):
        _log(tmp_path).record(trial=trial, agent="a", event_type=EventType.MODEL_CALL, content="x")
    assert [line["trial"] for line in _lines(_log(tmp_path))] == [0, 1]


def test_newlines_in_content_stay_on_one_line(tmp_path: Path) -> None:
    log = _log(tmp_path)
    log.record(trial=0, agent="a", event_type=EventType.TOOL_RESULT, content="one\ntwo")
    assert _lines(log)[0]["content"] == "one\ntwo"


def test_event_types_are_the_closed_set() -> None:
    assert {member.value for member in EventType} == {
        "model_call",
        "tool_call",
        "tool_result",
        "memory_read",
        "memory_write",
        "defense",
    }


def test_defense_event_records_the_layer(tmp_path: Path) -> None:
    log = _log(tmp_path)
    log.record(
        trial=0,
        agent="comms_agent",
        event_type=EventType.DEFENSE,
        content="recipient not allowed",
        defense=DefenseLayer.TOOL_PERMISSIONS,
    )
    assert _lines(log)[0]["defense"] == "tool_permissions"


def test_defense_event_without_a_layer_is_rejected(tmp_path: Path) -> None:
    log = _log(tmp_path)
    with pytest.raises(ValidationError, match="must name the layer"):
        log.record(trial=0, agent="a", event_type=EventType.DEFENSE, content="blocked")
    assert not log.path.exists()


def test_unknown_event_type_is_rejected() -> None:
    with pytest.raises(ValidationError, match="event_type"):
        Event(
            run_id="run-1",
            scenario_id="inj-001",
            trial=0,
            timestamp=FIXED_TIME,
            agent="a",
            event_type="made_up",
            content="x",
        )


def test_naive_timestamp_is_rejected(tmp_path: Path) -> None:
    log = EventLog(tmp_path, "run-1", "inj-001", clock=lambda: datetime(2026, 1, 2))
    with pytest.raises(ValidationError, match="timestamp"):
        log.record(trial=0, agent="a", event_type=EventType.MODEL_CALL, content="x")


@pytest.mark.parametrize("run_id", ["../escape", "a/b", "..", "", ".hidden", "run\n"])
def test_run_id_that_could_leave_the_log_dir_is_rejected(tmp_path: Path, run_id: str) -> None:
    with pytest.raises(ValueError, match="invalid run id"):
        _log(tmp_path, run_id)
