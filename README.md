# Patho Agent Synoptic

Patho Agent Synoptic is a collection of **rule-based pathology workflow demonstrations** with a Python CLI, an optional FastAPI service, and a static browser interface. It evaluates generic numeric thresholds and status-keyword flags in **synthetic** case records. It is not a validated CAP synoptic reporting engine.

## Browser demonstration

Open [web/index.html](web/index.html) directly in a modern browser to run the three rules locally, inspect the resulting JSON dossier, and export it. The page uses [web/app.js](web/app.js), not a server, and does not load Pyodide or transmit case data. Its numeric behavior matches the primary demonstration workers in **agents/workers.py**.

A GitHub Pages publication workflow is provided in **.github/workflows/pages.yml**. The Pages URL is intentionally not advertised until publishing has been enabled and the live application has been verified.

## Implemented demonstration rules

The primary **agents/** implementation and browser interface evaluate:

| Rule | Demonstration trigger | Output |
| --- | --- | --- |
| Primary measurement check | Primary metric > 25 | Elevated alert |
| Priority / secondary measurement check | Critical flag or secondary metric > 12 | Critical alert when manually flagged; otherwise elevated |
| Descriptor scan | Contains DISCORDANT, ANOMALY, MUTANT, VIOLATION, FAIL, or REJECT | Elevated alert |

These **unitless values are not clinical decision thresholds**. No specimen-specific CAP synoptic fields, staging criteria, margins, node counts, or ER/PR/HER2/Ki-67 assays are actually validated.

The repository also includes an older **patho_agent_synoptic/** implementation, the standalone **patho_synoptic.py** prototype, and auxiliary enrichment modules. Their thresholds and schemas differ; results from these interfaces must not be assumed interchangeable.

## Install and run

Requires Python 3.9 or newer.

~~~bash
python -m pip install -e ".[server,dev]"
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python cli.py audit --task-id DEMO-001 --target SYNTH-001 --primary 28.5 --secondary 14.2 --status DISCORDANT
python cli.py chat "What is the status?"
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
~~~

The primary CLI's **batch** command expects the **SystemTaskPayload** column names: task_id, target_identifier, primary_metric, secondary_metric, status_descriptor, is_critical_flag. Boolean cells accept true/false, yes/no, or 1/0.

The supplied [sample.csv](sample.csv) uses the **alternative packaged CLI** schema, so run it with:

~~~bash
python -m patho_agent_synoptic.cli batch -i sample.csv -o results.csv
~~~

For the primary CLI, **python cli.py serve** exposes GET /health, GET /metrics, POST /api/audit, POST /api/chat, and GET /api/audit/logs. **agents/api.py** is the service implementation. The installed **patho-engine-synoptic** command targets the separate packaged CLI instead. Do not expose either demonstration service on a public network without appropriate authentication, access control and deployment review.

### Container

~~~bash
printf 'AUDIT_SECRET_KEY=%s\n' "$(python -c 'import secrets; print(secrets.token_hex(32))')" > .env
docker compose up --build
~~~

Compose binds port 8000 on the host. Restrict network exposure; use only synthetic data.

## Security and data handling

- The primary Python CLI uses an in-memory HMAC-SHA256 hash-chain audit log. Verification recomputes signatures and detects modification within the current process. **This is not persistent, blockchain-anchored, or equivalent to an external immutable audit log.**
- The Python implementation has regex-based identifier detection. Such patterns cannot guarantee removal of protected health information, HIPAA compliance, or de-identification.
- The browser demonstration stores no form values in cookies, localStorage, or a backend. JSON output is downloaded only upon user action.
- The mock LLM returns deterministic test text. Actual OpenAI, Anthropic, and Ollama inference integrations are **not implemented**.
- The Python service keeps case summaries in process memory; restarting the process loses them.

## Testing

~~~bash
python -m pytest -v
node web/test-app.cjs
python -m compileall -q agents patho_agent_synoptic cli.py patho_synoptic.py
~~~

GitHub Actions runs the Python test suite on 3.10, 3.11 and 3.12, plus the static browser checks. The browser uses standard JavaScript, HTML and CSS without a build step and is intended for modern desktop and mobile browsers.

## License

[MIT](LICENSE).
