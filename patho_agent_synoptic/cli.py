"""
Command-Line Interface for PathoAgent Synoptic: Autonomous Surgical Pathology Synoptic Completeness & Biomarker Triager.
"""
import argparse
import csv
import json
import sys
from pathlib import Path
from .models import ClinicalCasePayload
from .agents import PathologyDirectorCoordinator

coordinator = PathologyDirectorCoordinator()


def _resolve_safe_path(file_path: str, must_exist: bool = False) -> Path:
    """Resolve a path safely, preventing directory traversal attacks."""
    try:
        resolved = Path(file_path).resolve()
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid path '{file_path}': {e}")

    cwd = Path.cwd().resolve()
    if not resolved.is_relative_to(cwd):
        raise ValueError(
            f"Path '{file_path}' resolves outside the working directory. "
            "Directory traversal is not permitted."
        )

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    return resolved



def _parse_bool(value) -> bool:
    """Parse boolean CSV fields without treating the string 'false' as true."""
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="patho-agent-synoptic", description="PathoAgent Synoptic: Autonomous Surgical Pathology Synoptic Completeness & Biomarker Triager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single case clinical audit")
    p_audit.add_argument("--case-id", default="CASE-2026-001")
    p_audit.add_argument("--primary", type=float, default=26.2)
    p_audit.add_argument("--secondary", type=float, default=12.5)
    p_audit.add_argument("--stat", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        case = ClinicalCasePayload(
            case_id=args.case_id,
            patient_synthetic_id="SYNTH-PT-881",
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_flag=args.status,
            is_stat=args.stat,
        )
        dossier = coordinator.process_case(case)
        print("=" * 80)
        print(f"  PATHOAGENT SYNOPTIC: AUTONOMOUS SURGICAL PATHOLOGY SYNOPTIC COMPLETENESS & BIOMARKER TRIAGER")
        print(f"  Domain: Digital Pathology | Standard: CAP Cancer Protocols & ASCO/CAP 2023")
        print(f"  Case: {dossier['case_id']} | Status: [{dossier['overall_status']}] | Total Alerts: {dossier['total_alerts']}")
        print("=" * 80)
        for a in dossier["alerts"]:
            print(f"\n  [{a['urgency']}] from {a['sub_agent']}:")
            print(f"  Title: {a['title']}")
            print(f"  Finding: {a['clinical_finding']}")
            print(f"  Action: {a['actionable_recommendation']}")
        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        ans = coordinator.query_supervisory_chat(" ".join(args.query))
        print(f"\n[PathologyDirectorCoordinator]:\n{ans}\n")
        return 0

    if args.command == "batch":
        input_path = _resolve_safe_path(args.input, must_exist=True)
        output_path = _resolve_safe_path(args.output, must_exist=False)

        with open(input_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = list(dict.fromkeys(fieldnames + ["overall_status", "total_alerts", "stat_critical_alerts", "consensus_summary"]))
        out_rows = []
        for r in rows:
            case = ClinicalCasePayload(
                case_id=r.get("case_id", "CASE-01"),
                patient_synthetic_id=r.get("patient_synthetic_id", "SYNTH-01"),
                primary_metric=float(r.get("metric_primary", r.get("primary_metric", 15.0))),
                secondary_metric=float(r.get("metric_secondary", r.get("secondary_metric", 5.0))),
                status_flag=r.get("status_flag", r.get("status_text", "NORMAL")),
                is_stat=_parse_bool(r.get("is_stat", r.get("critical_flag", False))),
            )
            dossier = coordinator.process_case(case)
            row_dict = dict(r)
            row_dict["overall_status"] = dossier["overall_status"]
            row_dict["total_alerts"] = dossier["total_alerts"]
            row_dict["stat_critical_alerts"] = dossier["stat_critical_alerts"]
            row_dict["consensus_summary"] = dossier["consensus_summary"]
            out_rows.append(row_dict)

        with open(output_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Batch processed {len(out_rows)} records -> {output_path}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from .server import create_app
            app = create_app()
            if app:
                print(f"Starting PathoAgent Synoptic: Autonomous Surgical Pathology Synoptic Completeness & Biomarker Triager on http://{args.host}:{args.port}")
                uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("FastAPI / uvicorn not installed. Run 'pip install fastapi uvicorn'")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
