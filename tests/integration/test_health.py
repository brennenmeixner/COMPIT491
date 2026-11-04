import pytest
from fastapi.testclient import TestClient

from agentsec.api.app import create_app


def test_health_responds_ok_without_any_model_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    response = TestClient(create_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/", "/docs", "/redoc", "/openapi.json"])
def test_only_health_is_served(path: str) -> None:
    assert TestClient(create_app()).get(path).status_code == 404


def test_health_sends_no_cors_headers() -> None:
    response = TestClient(create_app()).get("/health", headers={"Origin": "http://evil.test"})
    assert "access-control-allow-origin" not in response.headers
