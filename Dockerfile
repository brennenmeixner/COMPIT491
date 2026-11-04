FROM python:3.12-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app

# Dependencies first, so a source change does not reinstall them.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-editable


FROM python:3.12-slim-bookworm AS runtime
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin agentsec
WORKDIR /app

COPY --from=builder /app/.venv ./.venv
# src is here for ruff; the running code is the wheel installed in the venv.
COPY pyproject.toml ./
COPY config ./config
COPY data ./data
COPY scenarios ./scenarios
COPY src ./src
COPY tests ./tests
COPY web ./web

# Named volumes copy this ownership on first use, so the non-root user can write to them.
RUN mkdir -p logs outbox memory && chown -R agentsec:agentsec data logs outbox memory

ENV PATH="/app/.venv/bin:$PATH" \
    AGENTSEC_CONFIG_DIR=/app/config \
    AGENTSEC_SCENARIO_DIR=/app/scenarios \
    AGENTSEC_WEB_DIR=/app/web \
    HOME=/tmp \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RUFF_NO_CACHE=true

USER 10001
EXPOSE 8000

# 0.0.0.0 is inside the container only. Compose publishes the gateway on host loopback.
CMD ["uvicorn", "--factory", "agentsec.api.app:create_app", "--host", "0.0.0.0", "--port", "8000"]
