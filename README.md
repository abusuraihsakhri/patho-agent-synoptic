# Patho Agent Synoptic

> **Domain:** Digital Pathology & Quantitative Histopathology  
> **Reference Guidelines & Standards:** `College of American Pathologists (CAP) Synoptic Protocols & DICOM WSI`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Patho Agent Synoptic** is an advanced analytical and computational platform implementing Surgical Pathology CAP Cancer Protocol & Biomarker Completeness Agent.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`Severity`** — dedicated module for severity evaluation and state verification.
- **`DomainKnowledgeRegistry`**: Enterprise domain rules, guideline matrices, and evidence benchmarks.
- **`AgentAlert`** — dedicated module for agent alert evaluation and state verification.
- **`ScanQCAgent`**: Specialized Sub-Agent 1 for patho-agent-synoptic
- **`CAPProtocolValidatorAgent`**: Specialized Sub-Agent 2 for patho-agent-synoptic
- **`BiomarkerDiscordanceAgent`**: Specialized Sub-Agent 3 for patho-agent-synoptic

---

## 💻 CLI Quickstart & Usage

### 1. Run a Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Query the Supervisory Chat
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch Process CSV Records
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch the FastAPI REST Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### CLI Command Reference

| Command | Description | Key Flags |
|:--------|:------------|:----------|
| `audit` | Run single task evaluation | `--task-id`, `--target`, `--primary`, `--secondary`, `--critical`, `--status` |
| `chat` | Query supervisory assistant | `query` (positional) |
| `batch` | Batch process CSV records | `-i/--input`, `-o/--output` |
| `verify-audit` | Verify HMAC audit trail integrity | — |
| `serve` | Launch FastAPI REST server | `--host`, `--port` |

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task/case identifier | Required |
| `target_identifier` | Entity or specimen key | Required |
| `primary_metric` | Primary domain measurement | Required |
| `secondary_metric` | Secondary kinetic/confidence score | Optional (default: 0.0) |
| `status_descriptor` | Status code or phenotype | Optional (default: "NOMINAL") |
| `is_critical_flag` | Emergency escalation trigger | Optional (default: false) |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🔧 Prerequisites & Environment Variables

The following environment variable is **required** for cryptographic audit trail operation:

| Variable | Required | Description |
|:---------|:---------|:------------|
| `AUDIT_SECRET_KEY` | Yes | Secret key for HMAC-SHA256 audit trail signing (min 16 characters) |

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 🧪 Testing & Verification

Run the automated test suite:

```bash
AUDIT_SECRET_KEY=test-key-for-testing-only-12345 pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

### Docker Compose (Recommended)
Create a `.env` file with your audit secret key:
```bash
echo "AUDIT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" > .env
docker compose up --build
```

### Docker Direct
```bash
docker build -t patho-agent-synoptic .
docker run -e AUDIT_SECRET_KEY=your-secret-key -p 8000:8000 patho-agent-synoptic
```
