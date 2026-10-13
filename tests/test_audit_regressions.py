"""Regression coverage for audit integrity, task validation and CSV batch input."""
import csv
import math
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.llm_factory import LLMFactory
from cli import _parse_bool as parse_root_bool, _resolve_safe_path as root_safe_path, main as root_main
from patho_agent_synoptic.cli import _parse_bool as parse_package_bool, main as package_main
from patho_agent_synoptic.audit_trail import TamperEvidentAuditTrail


def test_audit_rejects_tampered_signed_field():
    trail = AuditTrail(secret_key="a-test-key-with-enough-entropy-for-tests")
    trail.log("tester", "reviewer", "TASK_FINISHED", {"id": "SYNTH"})
    assert trail.verify_integrity()
    trail.logs[0]["event_type"] = "MODIFIED"
    assert not trail.verify_integrity()



def test_audit_field_separator_substitution_is_detected():
    trail = AuditTrail(secret_key="a-test-key-with-enough-entropy-for-tests")
    trail.log("A|B", "C", "TASK_FINISHED", {"id": "SYNTH"})
    trail.logs[0]["actor"] = "A"
    trail.logs[0]["actor_tier"] = "B|C"
    assert not trail.verify_integrity()


def test_audit_rejects_tampered_final_hash():
    trail = AuditTrail(secret_key="a-test-key-with-enough-entropy-for-tests")
    trail.log("tester", "reviewer", "TASK_FINISHED", {"id": "SYNTH"})
    trail.logs[-1]["current_hash"] = "f" * 64
    assert not trail.verify_integrity()


def test_audit_log_is_defensive_copy():
    trail = AuditTrail(secret_key="a-test-key-with-enough-entropy-for-tests")
    trail.log("tester", "reviewer", "TASK_FINISHED", {"id": "SYNTH"})
    trail.get_trail()[0]["actor"] = "interloper"
    assert trail.verify_integrity()
    assert trail.get_trail()[0]["actor"] == "tester"



def test_packaged_audit_chain_detects_sequence_tampering():
    audit = TamperEvidentAuditTrail(secret_key="test-key-for-package-audit")
    entry = audit.log_event("CASE-01", "EVALUATION", {"synthetic": True})
    assert audit.verify_chain("CASE-01")["valid"]
    assert audit.get_audit_log("CASE-01", limit=0) == []
    entry.sequence = 99
    assert not audit.verify_chain("CASE-01")["valid"]


def test_packaged_audit_chain_detects_last_hash_tampering():
    audit = TamperEvidentAuditTrail(secret_key="test-key-for-package-audit")
    audit.log_event("CASE-01", "EVALUATION", {"synthetic": True})
    audit.last_hashes["CASE-01"] = "tampered"
    assert not audit.verify_chain("CASE-01")["valid"]


@pytest.mark.parametrize("parse", [parse_root_bool, parse_package_bool])
def test_csv_boolean_parser(parse):
    assert parse("False") is False
    assert parse("0") is False
    assert parse("true") is True
    assert parse("YES") is True
    assert parse("") is False
    with pytest.raises(ValueError):
        parse("maybe")


@pytest.mark.parametrize("field", ["primary_metric", "secondary_metric"])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_metrics_rejected(field, value):
    values = dict(task_id="T", target_identifier="SYNTH", primary_metric=10, secondary_metric=5)
    values[field] = value
    with pytest.raises(ValidationError):
        SystemTaskPayload(**values)


def test_nested_phi_rejected():
    payload = SystemTaskPayload(task_id="TASK-001", target_identifier="SPECIMEN-001",
                                primary_metric=10, attributes={"notes": {"identifier": "MRN-123456"}})
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_unsupported_model_provider_is_not_silently_mocked():
    with pytest.raises(ValueError, match="Unsupported model provider"):
        LLMFactory.create("openai")


def test_sibling_prefix_not_accepted(tmp_path, monkeypatch):
    workspace = tmp_path / "work"
    workspace.mkdir()
    sibling = tmp_path / "work-not-allowed"
    sibling.mkdir()
    monkeypatch.chdir(workspace)
    with pytest.raises(ValueError, match="traversal"):
        root_safe_path(str(sibling / "sample.csv"))


@pytest.mark.parametrize("run,flag,outfield", [
    (root_main, "is_critical_flag", "overall_urgency"),
    (package_main, "is_stat", "overall_status"),
])
def test_batch_false_is_not_critical(tmp_path, monkeypatch, run, flag, outfield):
    monkeypatch.chdir(tmp_path)
    source = Path("input.csv")
    with source.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "task_id", "case_id", "target_identifier", "primary_metric",
            "secondary_metric", "status_descriptor", "status_flag", flag
        ])
        writer.writeheader()
        writer.writerow(dict(task_id="TASK-01", case_id="CASE-01", target_identifier="SYNTH",
                             primary_metric="5", secondary_metric="2", status_descriptor="NOMINAL",
                             status_flag="NORMAL", **{flag: "False"}))
    assert run(["batch", "-i", str(source), "-o", "output.csv"]) == 0
    with open("output.csv", newline="", encoding="utf-8") as f:
        result = next(csv.DictReader(f))
    assert result[outfield] in {"ROUTINE", "CONCORDANT_NORMAL"}
