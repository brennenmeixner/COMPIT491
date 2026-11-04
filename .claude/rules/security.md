# Security rules

This project is a security lab. Its job is to attack its own system safely and measure the defenses. These rules keep the lab contained and keep the defenses honest.

## Containment

- Synthetic data only. No real people, customers, credentials, API keys or company documents anywhere in the repo, fixtures or logs.
- Tools are mocks or sandboxed local resources. `send_email` never sends anything: it appends to `outbox/emails.jsonl`. No tool opens a network connection except the app's call to the Ollama service.
- Attack payloads exist only as test fixtures under `data/docs/` and `scenarios/`, aimed at this system. Do not write attacks, payloads or scripts aimed at any real service, product or person.
- Bind the API to localhost by default. Never expose the baseline profile on a public address, including through Dokku. A Dokku deployment is for local or private use.
- The app container runs as a non-root user with a read-only root filesystem. Only the data, logs, outbox and memory volumes are writable, and its network reaches only the Ollama service.

## The baseline is intentionally weak

- The `baseline` profile leaves every defense off on purpose. Do not quietly harden it. Each deliberate weakness is listed in the threat model so nobody mistakes it for a bug.
- A vulnerability in the harness, the API, the oracles or the container itself is a real bug. Fix it and say so.

## Defense design

- Enforcement lives in ordinary code outside the model. Never rely on a system prompt instruction as a control.
- Default deny. The policy engine allows only what `config/policy.yaml` names: per-agent tool allowlists, path roots, recipient allowlist and call-count caps.
- Treat document text, database rows, tool output, memory notes written from those sources, and user prompts as untrusted data. Wrap them in labeled data blocks when they enter a prompt.
- File paths: resolve the path, then confirm it is inside the allowed root with `is_relative_to`. Reject symlinks that leave the root.
- SQL: parse with `sqlglot` and allow only a single `SELECT`. Open SQLite read-only (`mode=ro`) unless a scenario needs otherwise.
- Memory: only named agents may write. Every note carries source and trust labels. Untrusted notes are shown to a model as data, never as instructions. Notes expire.
- Output validation scans responses and outgoing emails for canary strings and PII patterns before they leave the system.
- Every block returns a typed decision with the layer name and reason, and is written to the event log.

## Code hygiene

- No `eval`, `exec`, `pickle` of untrusted data, or `subprocess` with `shell=True`.
- Validate every API input with pydantic. Never use a request value directly as a file path, SQL fragment or command.
- Secrets live in a gitignored `.env`. Never commit a secret, and never print one. Logs may contain canary strings and nothing else sensitive.
- Pin dependencies through `uv.lock`. Do not add a dependency without saying why.
- Keep CORS closed and do not add authentication shortcuts or debug backdoors to the API.
