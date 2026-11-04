# Project Outline: Securing Agentic AI Systems

COMP/IT 491 capstone, CSU Channel Islands. Team: Brennen Meixner (agent system), Jesus Mariano (security defenses), Alejandra Salazar (threat analysis and testing). Adviser: Dr. Reza Abdolee.

**Status: milestone 1 of 7 (the skeleton) is complete.** The containers, config loading, event log, CLI and health endpoint run and are tested. Agents, tools, attacks, defenses and the browser UI do not exist yet, so there are no security results.

## 1. What the project is

We are building a small multi-agent system so we can attack it, defend it and retest it in a controlled experiment. Each defense configuration will be measured on attack success rate, task completion, false blocks and added latency. The four attack types are prompt injection, unauthorized tool use, memory poisoning and data leakage.

The results will be evidence from this one experiment. They will not show that any control stops every attack.

Three priorities shape the project, in this order:

1. **Everything runs in Docker.** `docker compose` is the supported path.
2. **Results are reproducible.** Runs are seeded and logged, and code oracles score them rather than people reading model output.
3. **The baseline is deliberately weak.** Attacks need something to find, and defenses switch on one layer at a time through config.

## 2. Progress

| # | Milestone | Status |
| --- | --- | --- |
| 1 | Skeleton: Docker, config, event log, CLI, `/health`, tests | **Done** |
| 2 | Fixtures and tools: seed database, canaries, documents, five tools, `MemoryStore` | Not started |
| 3 | Agents and supervisor on the baseline, with a scripted stub model | Not started |
| 4 | Harness: scenarios, runner, oracles, benign suite, metrics | Not started |
| 5 | Defenses, one layer at a time | Not started |
| 6 | Full API and browser UI | Not started |
| 7 | Full evaluation on Ollama, report tables and screenshots | Not started |

## 3. What is built

### Files

```text
COMPIT491/
├── .claude/                  # project instructions and rules (CLAUDE.md, rules/)
├── config/
│   ├── models.yaml           # model and URL from the environment, plus temperature and seed
│   ├── defenses.yaml         # five layer flags, profiles baseline and all
│   └── policy.yaml           # tool allowlists, path roots, recipients, call caps
├── data/  scenarios/  web/   # empty placeholders for later milestones
├── docs/screenshots/         # captured outputs from real runs (section 7)
├── src/agentsec/
│   ├── config.py             # loads and validates the three YAML files
│   ├── event_log.py          # JSONL event writer and the closed event-type enum
│   ├── cli.py                # agentsec --help, agentsec check
│   ├── api/app.py            # FastAPI app with GET /health only
│   └── agents/ tools/ memory/ defenses/ harness/ evaluation/   # empty packages
├── tests/
│   ├── unit/                 # test_config.py, test_event_log.py, test_cli.py
│   └── integration/          # test_health.py, test_containment.py
├── Dockerfile  compose.yaml  # the container setup
├── pyproject.toml  uv.lock   # dependencies, pinned through the lock file
└── .env.example  .gitignore  .dockerignore
```

### Config (`config.py`)

`load_config(config_dir, env)` reads the three YAML files and validates them into frozen pydantic models. Unknown keys are rejected. The environment is passed in as an argument, so tests never depend on the real one.

- **`models.yaml`:** `model: ${OLLAMA_MODEL}` and `base_url: ${OLLAMA_BASE_URL}` are read from the environment. If either is unset or empty, loading raises `ConfigError` naming the variable. No default model exists anywhere in the code. `base_url` must be http or https and must not contain credentials. `temperature` is 0.0 and `seed` is 491.
- **`defenses.yaml`:** holds `active_profile` and the `profiles`, each with the five flags: `input_validation`, `output_validation`, `tool_permissions`, `memory_controls` and `sandbox`. Loading fails if `baseline` is not all off or `all` is not all on, so neither can drift quietly. **These flags change nothing yet, because no defense layer exists.**
- **`policy.yaml`:** holds per-agent tool allowlists, path roots, a recipient allowlist and call caps. The recipient list is empty, and the call caps (20 per run, 10 per tool) are placeholders. **Nothing enforces this file yet.** The policy engine arrives in milestone 5.

### Event log (`event_log.py`)

`EventLog` appends one JSON line per event to `<log_dir>/<run_id>.jsonl`.

- **Fields:** run id, scenario id, trial, timestamp, agent, event type, content and defense.
- **Event types:** a closed set of `model_call`, `tool_call`, `tool_result`, `memory_read`, `memory_write` and `defense`.
- **Validation:** a `defense` event must name the layer that acted, timestamps must carry a time zone, and a run id cannot contain path characters that would let it leave the log directory.

Nothing calls the logger in normal operation yet. Agents and tools will start using it in milestones 2 and 3.

### CLI (`cli.py`)

`agentsec check` prints the defenses, policy and models config, then requests `{base_url}/api/version` to see whether Ollama answers. It exits non-zero if any config section is invalid or Ollama is unreachable. It still checks Ollama when the model is unset, because the two problems are separate.

### API (`api/app.py`)

`create_app()` serves `GET /health` only. The OpenAPI and docs routes are turned off and no CORS is configured. `/health` doesn't load any config, so the app starts on a clean checkout before a model has been chosen.

## 4. Container architecture

```text
   host 127.0.0.1:8000
          |
      [ gateway ]  socat relay               edge network
          |
 =========|================================  backend network (internal, no route out)
      |              |              |
   [ app ]      [ ollama ]      [ test ]
   API + CLI         |          on demand
                     |
                  egress network (for pulling models)

 Optional: [ host-ollama ] relay on backend + egress, to Ollama on the host
```

| Service | Role | Networks |
| --- | --- | --- |
| `app` | API and CLI. UID 10001, read-only root, all capabilities dropped. Writable only at the `data`, `logs`, `outbox` and `memory` volumes and `/tmp`. | `backend` |
| `gateway` | Publishes the API on host loopback only. | `edge`, `backend` |
| `ollama` | Pinned official image, with models in a volume. No published port. | `backend`, `egress` |
| `test` | Same image and hardening as `app`, started on demand. Doesn't need Ollama. | `backend` |
| `host-ollama` | Optional relay (profile `host-ollama`) for Ollama on the host. | `backend`, `egress` |

**Why there is a `gateway`:** the security rules require the app's network to reach only Ollama, and the API must still be reachable from the host. Docker doesn't publish ports from an internal network, so a separate relay carries the one inbound path. The app container has no route out.

**The image:** a multi-stage `Dockerfile` installs dependencies with `uv` from the lock file, then copies the virtual environment into a slim runtime stage. `test` and `app` share one image, so pytest and ruff ship in the app image.

### Known containment gap

The app can't reach the internet directly, but it can call Ollama's API, and Ollama has outbound access for pulling models. A compromised app could ask Ollama to pull or push through a registry. This needs a decision before attack runs, for example detaching `egress` once models are pulled.

## 5. How the pieces work together

### What happens today

1. `docker compose build` installs the locked dependencies into one image.
2. `docker compose up` starts `app` and `ollama`. Once the `app` healthcheck passes, `gateway` starts.
3. A request to `127.0.0.1:8000/health` goes through `gateway`, across `backend`, to `app`.
4. `agentsec check` runs inside the container. `config.py` loads the YAML and environment values into typed models, then the CLI prints them and tests the connection to Ollama.
5. `docker compose run --rm test` runs the tests in the same image with the same hardening, so the containment tests check real container settings.

### The planned system (not built)

```text
 user task or attack scenario
          |
          v
   Orchestrator (routes only)
      |            |            |
      v            v            v
  Document       Data         Comms
   Agent         Agent        Agent
  read_file     query_db     send_email
  list_files                 write_file
      |            |            |
      v            v            v
  data/docs/    test.db      outbox/
  (main injection            (exfiltration
   entry point)               sink)

 Around all of it:
   Policy engine   wraps every tool, model and memory call
   MemoryStore     shared SQLite notes with source and trust labels
   Canaries        unique strings that reveal leaks by exact match
   Event log       one JSON line per event, always on
```

| Piece | Planned role | Depends on what's built |
| --- | --- | --- |
| Tools | Local mocks only. `send_email` appends to `outbox/emails.jsonl` and sends nothing. | Path roots from `policy.yaml`, events through `EventLog` |
| `MemoryStore` | Keyword lookup over labeled notes, wiped before every run | Events through `EventLog`, writable `memory` volume |
| Agents | LangChain 1.x supervisor pattern, with a scripted stub model for tests | Model, URL, seed and temperature from `ModelsConfig` |
| Policy engine | Five layers in ordinary code outside the model, default deny | Flags from `DefensesConfig`, rules from `PolicyConfig`, `defense` events |
| Harness | Replays YAML scenarios for N trials, then scores them with code oracles | Reads the JSONL logs and the outbox |
| Metrics | Rates and tables generated from logs, never typed by hand | Reads the JSONL logs |
| API and UI | Five endpoints, a run console and a results screen | Extends `create_app()`, replaces the current lack of a UI |

## 6. Test results

From the last run on this code, using `docker compose run --rm test`: **46 passed.** `ruff check` and `ruff format --check` both pass.

| Test file | Tests | Covers |
| --- | --- | --- |
| `unit/test_config.py` | 17 | Valid load, unset model and URL, bad URLs, unknown keys, non-boolean flags, tampered or missing profiles, missing files, bad YAML |
| `unit/test_event_log.py` | 14 | Line format, append behaviour, closed event types, defense layer required, unsafe run ids |
| `unit/test_cli.py` | 6 | Help, reachable and unreachable Ollama, unset model, rejected URLs |
| `integration/test_health.py` | 6 | `/health`, no other routes, no CORS headers |
| `integration/test_containment.py` | 3 | Non-root, read-only root, no outbound route |

These tests cover the skeleton only and say nothing yet about attacks or defenses. The same checks also passed on a copy of only the files git would track, with no `.env` and no existing image. The containment tests run in `test`. The same checks were also run by hand against the live `app` container.

## 7. Captured outputs (`docs/screenshots/`)

Everything here comes from real runs of the Docker build.

**There is no UI screenshot because the UI doesn't exist yet.** It arrives in milestone 6. The two images below show the only things a browser can see today.

| File | What it shows |
| --- | --- |
| `health-endpoint-browser.png` | `/health` in headless Chrome |
| `root-no-ui-yet-404.png` | `/` returning 404, because no UI is served |
| `logs/pytest.txt` | The test run |
| `logs/ruff.txt` | Lint and format checks |
| `logs/compose-ps.txt` | Running services and the loopback-only port |
| `logs/health-response.txt` | Full `/health` HTTP response |
| `logs/app-container.log` | Uvicorn output from `app` |
| `logs/agentsec-check-model-unset.txt` | `agentsec check` failing clearly with no model set |
| `logs/container-containment.txt` | Hand-run checks on the live `app`: UID, read-only root, volumes, blocked traffic |
| `logs/event-log-demo.jsonl` | **Demo only.** Two hand-written events showing the real logger's format. No agent or defense ran. |
| `logs/ollama-benchmark-partial.txt` | The interrupted model benchmark (section 8) |

## 8. Model benchmark on the target machine

The target is an Intel NUC with a Celeron N5105 (4 cores), 32 GB RAM and no usable GPU. The CPU has SSE4.2 but no AVX or AVX2, which rules out the fast inference paths. Memory is not the limit, because these models need less than 2 GB.

Each model got 4 simple tool-call prompts, run twice, with all five tools defined. Ollama ran in its container at temperature 0 and seed 491. **The run was stopped early, so `granite4:350m` has only one result.**

| Model | Correct tool | Median per call | Notes |
| --- | --- | --- | --- |
| `qwen3:0.6b` | 8 of 8 | 54.8s | Arguments looked correct. Range was about 36 to 259s. |
| `llama3.2:1b` | 8 of 8 | 9.1s | Both `send_email` calls had malformed arguments, nested inside a `parameters` object, so only 6 of 8 calls were usable. |
| `granite4:350m` | 1 of 1 | Not enough data | Stopped after one call, which took 72.2s including the model's first load. |

The first call for each model also takes 54 to 74s, mostly to process the full prompt.

These are small samples of simple, benign prompts. They don't predict how the models will behave under attack.

**Runtime is the concern.** As an illustration, assume 5 model calls per task (a guess, since no agents exist to measure), 10 trials and 7 configurations. That is 70 runs per scenario:

| Model | Per task | Per scenario |
| --- | --- | --- |
| `llama3.2:1b` | About 45s | About 52 minutes |
| `qwen3:0.6b` | About 4.6 minutes | About 5.3 hours |

Twenty trials per scenario would double these figures. The machine can run the system, but a full evaluation could take days.

## 9. Open decisions

- **Default model:** not chosen, and `OLLAMA_MODEL` stays unset. Neither model tested so far is a clear winner: one is fast with bad `send_email` arguments, the other is accurate and slow. Possible next steps are finishing the `granite4:350m` run and trying `qwen3` with thinking turned off, which may explain its slowest calls but hasn't been confirmed.
- **Where Ollama runs:** this machine uses the container, since it has no GPU to pass through. The host path is wired up but has only been tested against a stub listener. Other team members' machines are unconfirmed.
- **Trials per scenario:** start with 10, and raise to 20 for final numbers only if runtime allows.
- **Dokku:** the local domain name, and whether it must be reachable beyond one machine. The baseline profile must never be exposed publicly.
- **Indirect egress through Ollama:** see section 4.

### Issues for later milestones

- With a fixed seed and temperature 0, trials may all come out identical, which would make N trials meaningless. Milestone 4 needs a per-trial seed rule.
- `testing.md` wants seed and temperature in every run's log, but the event schema has no field for them.
- A named volume on `/app/data` keeps old fixtures after a rebuild, which milestone 2 needs to handle.
- `compose.gpu.yaml` and `app.json` appear in the planned layout but aren't created yet.

## 10. How to run it

```bash
docker compose build
docker compose run --rm test
docker compose run --rm test ruff check .
docker compose up -d
curl http://127.0.0.1:8000/health
docker compose exec app agentsec check    # exits 1 until OLLAMA_MODEL is set
docker compose down
```

See `README.md` for connecting a model and running Ollama on the host.
