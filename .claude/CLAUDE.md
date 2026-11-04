# Securing Agentic AI Systems

COMP/IT 491 capstone at CSU Channel Islands. Team: Brennen Meixner (builds the agent system), Jesus Mariano (security defenses), Alejandra Salazar (threat analysis and testing). Adviser: Dr. Reza Abdolee.

## What this project is

A small multi-agent system that we build, attack, defend and retest. For every defense configuration we measure attack success rate, task completion and false blocks. The four attack types are prompt injection, unauthorized tool use, memory poisoning and data leakage. Results are evidence from a controlled experiment. Never write code, docs or UI copy that claims a control stops every attack.

## Priorities, in order

1. Everything runs in Docker. `docker compose` is the supported path and must work first; all deliverable testing uses it. Dokku is an optional layer that serves the same app at a local domain name. Compose alone must pass every test.
2. Reproducible: seeded, logged, and scored by code oracles, never by reading model output by eye.
3. The baseline is intentionally permissive so attacks have something to find. Defenses are switched on and off by config, one layer at a time.

## Architecture

- **Four agents** on LangChain 1.x with a supervisor pattern (LangGraph underneath): Orchestrator (routes only), Document Agent (read_file, list_files), Data Agent (query_db), Comms Agent (send_email, write_file). The Document Agent is the main injection entry point. The Comms Agent is the exfiltration sink.
- **Tools are mocks or sandboxed local resources.** read_file and list_files use `data/docs/`. query_db uses SQLite `data/test.db`. send_email only appends to `outbox/emails.jsonl`. write_file only writes under `outbox/`.
- **Shared memory** is a SQLite store behind one `MemoryStore` class. Each note records content, writing agent, source (user, document, tool, agent), trust label, timestamp and run id. Keyword lookup in v1, no embeddings. Wiped and reseeded before every run.
- **Policy engine** wraps every tool call, model call and memory access. It is ordinary code outside the model. Five layers, each with its own flag in `config/defenses.yaml`: input validation, output validation, tool permissions, memory controls, sandbox. Logging is always on.
- **Canaries:** protected values are unique strings such as `CANARY-7F3A`, planted in the database, a private document and memory. Leakage is detected by exact-match search of responses and the outbox.
- **Harness** replays YAML scenarios with a fixed seed and temperature, runs N trials, and scores each with an oracle. A benign suite measures normal task completion and false blocks.
- **API and UI:** a FastAPI service serves the browser UI and five endpoints: `POST /runs`, `GET /runs/{id}/events` (live stream), `GET /scenarios`, `GET /config/defenses`, `GET /results`.

## Services (Compose)

| Service | Role |
| --- | --- |
| app | Built from the repo Dockerfile. API, UI, agents, tools, defenses, harness. Non-root user, read-only root filesystem, writable volumes only for data, logs, outbox and memory. |
| ollama | Official Ollama image, models in a volume. May run on the host instead; selected with `OLLAMA_BASE_URL`. |
| test | Same image as app. Runs the tests. Started on demand only. |

## Commands (proposed, adjust when the repo exists)

```bash
docker compose up --build        # app and ollama; UI on the published port
docker compose run --rm test     # unit, integration and scenario tests
docker compose run --rm app agentsec run scenarios/attacks/inj-001.yaml --defenses all
```

## Repository layout

```text
COMPIT491/
├── .claude/                 # CLAUDE.md and rules/
├── config/                  # models.yaml, defenses.yaml, policy.yaml
├── data/                    # docs/, private/, seed_db.sql (test.db is generated)
├── scenarios/               # attacks/ and benign/ YAML files
├── src/agentsec/            # agents/, tools/, memory/, defenses/, harness/, evaluation/, api/
├── web/                     # browser UI served by the API
├── tests/                   # unit/ and integration/
├── outbox/  logs/           # runtime output, gitignored
├── Dockerfile  compose.yaml  compose.gpu.yaml  app.json
└── pyproject.toml  uv.lock  README.md
```

## Metrics

- **Attack success rate:** successful trials divided by total trials, per attack type. Lower is better.
- **Task completion rate:** benign tasks passing their expected-output check, divided by benign tasks. Higher is better.
- **False block rate:** legitimate tool calls or messages blocked by a defense, divided by legitimate attempts. Lower is better.
- **Added latency:** median seconds per task with defenses, minus baseline.

Every run writes one JSON line per event to `logs/`: run id, scenario id, trial, timestamp, agent, event type (model call, tool call, tool result, memory read, memory write, defense decision), content, and the defense that acted. Report tables and screenshots are generated from these files, never typed by hand.

## UI spec

Two screens, plain HTML, CSS and JavaScript served by the API, no framework and no build step. The look is a terminal.

| Screen | Contents |
| --- | --- |
| Run console | Scenario list as text radios `(*)`, five defense toggles as `[x]` buttons, `baseline` and `all` shortcuts, trials input, `[ run ]`, a live event log with `└` notes under lines a defense acted on, a result line (`ATTACK SUCCEEDED` or `ATTACK BLOCKED`), and a status bar. |
| Results | Attack success rate grid (attack type by baseline, input, output, tools, memory, sandbox, all), a normal-tasks table (completed, false blocks, added latency), and a status bar with seed, model and trial counts. Cells show `-` until data exists. |

Style: monospace; background `#101010`, text `#D8D8D8`, dim `#8C8C8C`, ok `#86D993`, bad `#F28B82`; square boxed panels (fieldset and legend); inverse-video status bar; no rounded corners, cards, pills, icons, gradients or shadows; real `<button>` elements with at least 44px tap height; every number comes from the API, never invented.

## Decisions not settled yet

Do not guess these. Put them in config, use a clearly marked placeholder, and ask the team.

- Default Ollama model (must support tool calling) and the team's RAM or GPU memory.
- Whether Ollama runs in a container or on the host (Docker Desktop on macOS may not pass a GPU into containers; to confirm).
- Local domain name for Dokku, and whether it must be reachable beyond one machine. Dokku needs a Linux host or VM.
- Trials per scenario: start with 10, raise to 20 for final numbers if runtime allows.
- Vector store for memory: not in v1.
- Schedule length: the proposal says 8 weeks, the README says 20. This does not affect the code.

## Build order

1. Skeleton: Dockerfile, compose.yaml, pyproject, uv lock, config loading, event log, a passing smoke test in the test container.
2. Fixtures and tools: seed database with canaries, documents including injected ones, the five tools, MemoryStore.
3. Agents and supervisor on the baseline (all defenses off), with a scripted stub model for tests.
4. Harness: scenario loader, runner, oracles, benign suite, metrics, results files.
5. Defenses, one layer at a time, each behind its own flag and with its own tests.
6. API and UI.
7. Full evaluation run on Ollama, report tables and screenshots from the logs.

## Working agreements

- Plan before large changes. Keep commits small and focused.
- Do not add a dependency without saying why. Pin through `uv.lock`.
- Run `ruff` and the test container before saying a task is done.
- Never commit `data/test.db`, `logs/`, `outbox/`, `.env` or model files.
- Keep `README.md` accurate to what actually runs.
- Follow the rules in `.claude/rules/`: `code-style.md`, `security.md`, `testing.md`.
