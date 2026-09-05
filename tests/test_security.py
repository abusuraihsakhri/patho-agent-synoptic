"""
Security and edge case tests for Patho Agent Synoptic.
Tests PHI guard, audit trail integrity, path traversal protection, and input validation.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import (
    PHIGuard,
    AuditLogger,
    AuditTrail,
    SecurityException,
    assert_no_phi,
)
from agents.models import SystemTaskPayload, UrgencyLevel
from agents.supervisor import SystemSupervisor


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_audit():
    """Reset global audit state before each test."""
    AuditLogger.reset()
    os.environ["AUDIT_SECRET_KEY"] = "test-key-for-testing-only-12345"
    yield
    AuditLogger.reset()


@pytest.fixture
def supervisor():
    os.environ["AUDIT_SECRET_KEY"] = "test-key-for-testing-only-12345"
    return SystemSupervisor(model_provider="mock")


# ---------------------------------------------------------------------------
# PHI Guard Tests
# ---------------------------------------------------------------------------

class TestPHIGuard:
    def test_ssn_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient SSN: 123-45-6789")

    def test_mrn_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("MRN-994827 blood culture positive")

    def test_phone_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at 555-123-4567")

    def test_email_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Send results to doctor@hospital.org")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("Task evaluation completed successfully")

    def test_empty_text_passes(self):
        PHIGuard.assert_no_phi("")

    def test_none_handled(self):
        PHIGuard.assert_no_phi(None)

    def test_redact_phi(self):
        redacted = PHIGuard.redact_phi("Contact patient at 555-123-4567 for results")
        assert "555-123-4567" not in redacted
        assert "[REDACTED_IDENTIFIER]" in redacted

    def test_redact_preserves_clean_text(self):
        clean = "Analytical specimen KEY-001 optimal result"
        assert PHIGuard.redact_phi(clean) == clean


# ---------------------------------------------------------------------------
# Audit Trail Tests
# ---------------------------------------------------------------------------

class TestAuditTrail:
    def test_missing_secret_key_raises(self):
        original = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with pytest.raises(SecurityException, match="AUDIT_SECRET_KEY"):
                AuditTrail()
        finally:
            if original:
                os.environ["AUDIT_SECRET_KEY"] = original

    def test_short_secret_key_raises(self):
        os.environ["AUDIT_SECRET_KEY"] = "short"
        with pytest.raises(SecurityException, match="at least 16"):
            AuditTrail()

    def test_explicit_key_works(self):
        trail = AuditTrail(secret_key="explicit-test-key-1234567890")
        entry = trail.log("actor", "tier", "EVENT", {"key": "value"})
        assert entry["current_hash"] != ""
        assert entry["prev_hash"] == "GENESIS_BLOCK_0000000000000000"

    def test_integrity_verification(self):
        os.environ["AUDIT_SECRET_KEY"] = "test-key-for-testing-only-12345"
        trail = AuditTrail()
        trail.log("a", "t", "E1", {"x": 1})
        trail.log("b", "t", "E2", {"y": 2})
        trail.log("c", "t", "E3", {"z": 3})
        assert trail.verify_integrity() is True

    def test_phi_in_audit_details_blocked(self):
        os.environ["AUDIT_SECRET_KEY"] = "test-key-for-testing-only-12345"
        trail = AuditTrail()
        with pytest.raises(SecurityException):
            trail.log("actor", "tier", "EVENT", {"note": "Patient SSN: 123-45-6789"})


# ---------------------------------------------------------------------------
# Supervisor Integration Tests
# ---------------------------------------------------------------------------

class TestSupervisorSecurity:
    def test_phi_in_task_id_blocked(self, supervisor):
        payload = SystemTaskPayload(
            task_id="MRN-994827-case",
            target_identifier="KEY-01",
            primary_metric=10.0,
        )
        with pytest.raises(SecurityException):
            supervisor.process_task(payload)

    def test_phi_in_target_blocked(self, supervisor):
        payload = SystemTaskPayload(
            task_id="TASK-01",
            target_identifier="Patient John Doe record",
            primary_metric=10.0,
        )
        with pytest.raises(SecurityException):
            supervisor.process_task(payload)

    def test_normal_task_processed(self, supervisor):
        payload = SystemTaskPayload(
            task_id="TASK-NORMAL-01",
            target_identifier="SPECIMEN-01",
            primary_metric=10.0,
            secondary_metric=4.0,
            status_descriptor="NOMINAL",
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency == UrgencyLevel.ROUTINE
        assert dossier.audit_hash != ""

    def test_audit_trail_verifiable_after_tasks(self, supervisor):
        payload = SystemTaskPayload(
            task_id="TASK-AUDIT-01",
            target_identifier="SPECIMEN-01",
            primary_metric=10.0,
        )
        supervisor.process_task(payload)
        assert AuditLogger.verify_integrity() is True


# ---------------------------------------------------------------------------
# Path Traversal Protection Tests
# ---------------------------------------------------------------------------

class TestPathTraversalProtection:
    def test_safe_path_within_cwd(self):
        from cli import _resolve_safe_path
        result = _resolve_safe_path("sample.csv", must_exist=False)
        assert result == Path("sample.csv").resolve()

    def test_traversal_blocked(self):
        from cli import _resolve_safe_path
        with pytest.raises(ValueError, match="traversal"):
            _resolve_safe_path("../../etc/passwd", must_exist=False)

    def test_traversal_with_symlink_blocked(self):
        from cli import _resolve_safe_path
        with pytest.raises(ValueError, match="traversal"):
            _resolve_safe_path("/etc/passwd", must_exist=False)

    def test_nonexistent_input_raises(self):
        from cli import _resolve_safe_path
        with pytest.raises(FileNotFoundError):
            _resolve_safe_path("nonexistent_file.csv", must_exist=True)


# ---------------------------------------------------------------------------
# Edge Case Tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_metrics(self, supervisor):
        payload = SystemTaskPayload(
            task_id="TASK-ZERO",
            target_identifier="KEY-ZERO",
            primary_metric=0.0,
            secondary_metric=0.0,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency == UrgencyLevel.ROUTINE
        assert dossier.total_alerts == 0

    def test_negative_metrics_accepted(self, supervisor):
        payload = SystemTaskPayload(
            task_id="TASK-NEG",
            target_identifier="KEY-NEG",
            primary_metric=-5.0,
            secondary_metric=-2.0,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency == UrgencyLevel.ROUTINE

    def test_very_large_metrics(self, supervisor):
        payload = SystemTaskPayload(
            task_id="TASK-LARGE",
            target_identifier="KEY-LARGE",
            primary_metric=999999.0,
            secondary_metric=999999.0,
            status_descriptor="DISCORDANT",
            is_critical_flag=True,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency == UrgencyLevel.CRITICAL_STAT
        assert dossier.critical_alerts_count > 0

    def test_special_characters_in_status(self, supervisor):
        payload = SystemTaskPayload(
            task_id="TASK-SPEC",
            target_identifier="KEY-SPEC",
            primary_metric=10.0,
            status_descriptor="DISCORDANT_ANOMALY",
        )
        dossier = supervisor.process_task(payload)
        assert dossier.total_alerts > 0
