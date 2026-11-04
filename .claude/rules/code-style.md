---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
  - "web/**"
  - "Dockerfile"
  - "compose*.yaml"
---

# Code style

## Python

- Python 3.11 or newer. Type hints on every function signature and public attribute.
- Format and lint with `ruff` (line length 100). No unused imports, no wildcard imports.
- Use pydantic models for tool arguments, config files, scenario files and log events. Validate at the boundary, then pass typed objects inward.
- No module-level mutable state. Pass dependencies (config, event logger, memory store, policy engine, model) into constructors or functions.
- All output goes through `event_log.py`. No `print` in library code. The CLI may use `rich` for display only.
- Configuration comes from `config/*.yaml` through `config.py`. Never hardcode a model name, path root, recipient or defense flag in code.
- Every source of randomness takes a seed from config. Model temperature comes from `config/models.yaml`.
- Small functions with one job. A function that both decides and acts gets split, so the decision can be tested alone.
- Raise specific exceptions. A defense that blocks something raises or returns a typed `Blocked` decision with the layer name and a reason. It never fails silently.
- Docstrings only where the name does not already say it. Comments explain why, not what.

## Naming and structure

- Package `agentsec`. Modules are lowercase with underscores. One agent per file under `agents/`, one defense layer per file under `defenses/`, one tool per file under `tools/`.
- Event types are a closed enum: `model_call`, `tool_call`, `tool_result`, `memory_read`, `memory_write`, `defense`.
- Scenario files are named `<attack>-<nnn>.yaml`, for example `inj-001.yaml`. Benign tasks are `ben-<nnn>.yaml`.

## Web (`web/`)

- Plain HTML, CSS and JavaScript. No framework, no bundler, no build step.
- Live events use `EventSource` against `GET /runs/{id}/events`.
- Follow the UI spec in `CLAUDE.md`: terminal look, real `<button>` elements, at least 44px tap height, no rounded corners, cards, pills, icons, gradients or shadows.
- Render API data as text with `textContent`. Never build markup from model output or log content with `innerHTML`.

## Docker

- Multi-stage Dockerfile. Install with `uv` from the lock file. The final stage runs as a non-root user with a read-only root filesystem.
- Compose files hold no secrets. Settings such as `OLLAMA_BASE_URL` come from environment variables with safe defaults.
- Keep `compose.yaml` working on CPU. GPU settings live in `compose.gpu.yaml`.
