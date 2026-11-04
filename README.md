# Securing Agentic AI Systems  
### Threat Modeling and Defense Evaluation

## Team Members

- Brennen Meixner
- Jesus Mariano
- Alejandra Salazar

## Project Overview

Agentic AI systems combine large language models with tools, memory, APIs, and multi-step decision-making. These systems can do more than generate text; they can access information, execute functions, use external tools, and communicate with other agents.

These capabilities also introduce new cybersecurity risks. Malicious or untrusted instructions may influence an agent, cause tool misuse, expose stored information, or affect how agents communicate and make decisions.

This project will develop a limited multi-agent AI system and evaluate its security against selected attack methods. After identifying weaknesses, we will implement safeguards and retest the system to determine whether the protections reduce successful attacks without preventing the agents from completing their intended tasks.

## Problem Statement

As agentic AI systems become more widely used, their ability to interact with tools, memory, and external resources creates additional attack surfaces.

Traditional security controls may not fully address attacks that target how AI agents interpret instructions and make decisions. This project will examine security risks in a controlled multi-agent system and evaluate defensive controls designed to reduce those risks.

## Project Goals and Objectives

The main goals of the project are to:

- Define the components, assets, trust boundaries, and risks of the system.
- Build a repeatable multi-agent AI prototype.
- Test selected attack scenarios against the system.
- Identify security weaknesses within the agent workflow.
- Implement safeguards around tools, memory, inputs, outputs, and agent actions.
- Retest the system after the safeguards are added.
- Compare security results before and after the defenses are implemented.
- Evaluate whether security improvements affect normal agent functionality.

## Proposed Features and System Components

The proposed system may include:

- Multiple AI agents with separate responsibilities
- Local large language model
- Agent orchestration
- Controlled tools and APIs
- File access
- Test database access
- Memory components
- Logging of agent actions and tool requests
- Input and output validation
- Tool permission controls
- Memory restrictions
- Controlled security testing environment

The team may adjust the exact components as the project develops and is evaluated.

## Planned Technologies and Tools

- **Python** — primary programming language
- **LangChain** — agent orchestration and multi-agent workflow development
- **Ollama** — running large language models locally
- **GitHub** — version control, project organization, and documentation
- **Local development environment** — controlled environment for development and security testing

We may add additional tools as the project progresses.

## Initial Implementation Plan and Timeline

### Weeks 1–4: Research and Scope

- Review research related to agentic AI security.
- Define the system architecture and scope.
- Identify assets, trust boundaries, and selected attack scenarios.
- Finalize the initial threat model.

### Weeks 5-12: Prototype and Baseline + Defense Implementation

- Build the initial multi-agent system.
- Configure the selected tools, data, and memory components.
- Establish logging and repeatable test conditions.
- Perform baseline security testing.
- Add selected safeguards.
- Implement tool permission controls.
- Add input, output, and memory protections.

### Weeks 13-16: Evaluation

- Repeat the selected attack scenarios.
- Record security and task-performance results.
- Compare baseline and defended results.
- Identify which safeguards were effective.

### Week 17-20: Analysis and Delivery

- Analyze final results.
- Document findings and limitations.
- Complete project documentation.
- Prepare the final report and demonstration.

## Expected Outcome

The project is expected to produce a documented threat model, a reproducible multi-agent prototype, controlled security test cases, implemented safeguards, and a comparison of baseline and defended results.

The final evaluation will identify which safeguards improved security, whether legitimate tasks were affected, and where additional testing or security controls may be needed.

## Quick Start

You need Docker with Compose. Everything runs in containers.

```bash
docker compose build             # build the image
docker compose run --rm test     # run the tests; needs no model and no network
docker compose up -d             # start the app, its gateway and Ollama
curl http://127.0.0.1:8000/health
docker compose down
```

While it's running, the browser UI is at http://127.0.0.1:8000/. The API and UI are published on `127.0.0.1` only. Set `APP_PORT` to use a port other than 8000. Compose does not rebuild an existing image, so run `docker compose build` after changing the code.

### Connect a model

No default model is chosen yet, so copy `.env.example` to `.env` and set `OLLAMA_MODEL` to a model that supports tool calling. `/health` works without it. Commands that need a model fail and name the missing variable.

```bash
docker compose exec ollama ollama pull "$OLLAMA_MODEL"   # needs OLLAMA_MODEL in your shell
docker compose run --rm app agentsec check               # prints config and Ollama status
```

`agentsec check` exits non-zero if the config is invalid or Ollama is unreachable.

### Run Ollama on the host

The app has no route out of its internal network, so host Ollama is reached through a relay. Ollama must listen on the Docker bridge, not only on loopback (for example `OLLAMA_HOST=0.0.0.0`, on a machine whose firewall keeps that port private). In `.env`, set:

```bash
OLLAMA_BASE_URL=http://host-ollama:11434
```

Then start only the services you need:

```bash
docker compose --profile host-ollama up -d app gateway host-ollama
```

### Container layout

| Service | Role | Networks |
| --- | --- | --- |
| `app` | API. Non-root, read-only root filesystem, writable volumes for data, logs, outbox and memory | `backend` |
| `gateway` | Relays `127.0.0.1:8000` on the host to the app | `edge`, `backend` |
| `ollama` | Official Ollama image, models in a volume | `backend`, `egress` |
| `test` | Same image as `app`, started on demand | `backend` |
| `host-ollama` | Optional relay to Ollama on the host (profile `host-ollama`) | `backend`, `egress` |

`backend` is an internal network, so `app` and `test` have no direct route out. `ollama` keeps outbound access for pulling models.

### Lint

```bash
docker compose run --rm test ruff check .
docker compose run --rm test ruff format --check .
```

### Tests outside Docker

Docker is the supported path. The containment tests describe the container, so exclude them on a host:

```bash
uv run pytest -m "not llm and not container"
```

## Project Status

**Current Phase:** Milestone 1, the project skeleton

So far this is the config loader, event log, `agentsec check` command, read-only API endpoints, the browser UI's two screens and the containers. Agents, tools, attack scenarios, defenses and the harness are not built yet, so the UI shows empty states and a run can't be started. Defense flags exist in `config/defenses.yaml` and the UI, but do not change anything until the layers are implemented.

`Securing the Agent UI.html` is the design mock for the UI. Its sample attack is scripted, not a real result. See `outline.md` for the full project outline.
