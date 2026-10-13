"""
Tamper-Evident Audit Trail for Patho Agent Synoptic.
HMAC-SHA256 secured in-memory logging with hash-chain integrity checks.
"""
import hashlib
import hmac
import json
import os
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class AuditEntry:
    """Single audit trail entry with HMAC integrity."""
    sequence: int
    event_type: str
    case_id: str
    details: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    prev_hash: str = "GENESIS"
    entry_hash: str = ""

    def compute_hash(self, secret_key: str) -> str:
        payload = json.dumps({
            "sequence": self.sequence,
            "event_type": self.event_type,
            "case_id": self.case_id,
            "details": self.details,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
        }, sort_keys=True)
        return hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()


class TamperEvidentAuditTrail:
    """HMAC-SHA256 secured audit trail with hash chaining."""

    def __init__(self, secret_key: Optional[str] = None):
        key = secret_key or os.getenv("AUDIT_SECRET_KEY")
        if not key:
            raise ValueError(
                "AUDIT_SECRET_KEY environment variable is required. "
                "Set a cryptographically random key before starting the application."
            )
        if len(key) < 16:
            raise ValueError("AUDIT_SECRET_KEY must be at least 16 characters long.")
        self.secret_key = key
        self.chains: Dict[str, List[AuditEntry]] = {}
        self.last_hashes: Dict[str, str] = {}

    def log_event(self, case_id: str, event_type: str, details: Dict[str, Any]) -> AuditEntry:
        prev_hash = self.last_hashes.get(case_id, "GENESIS")
        entry = AuditEntry(
            sequence=len(self.chains.get(case_id, [])),
            event_type=event_type,
            case_id=case_id,
            details=details,
            prev_hash=prev_hash,
        )
        entry.entry_hash = entry.compute_hash(self.secret_key)
        self.chains.setdefault(case_id, []).append(entry)
        self.last_hashes[case_id] = entry.entry_hash
        return entry

    def verify_chain(self, case_id: str) -> dict:
        chain = self.chains.get(case_id, [])
        if not chain:
            return {"valid": True, "entries": 0, "message": "No entries to verify"}

        prev_hash = "GENESIS"
        for i, entry in enumerate(chain):
            expected_hash = entry.compute_hash(self.secret_key)
            if not hmac.compare_digest(entry.entry_hash, expected_hash):
                return {"valid": False, "entries": len(chain), "failed_at": i, "message": f"Hash mismatch at sequence {i}"}
            if entry.prev_hash != prev_hash or entry.sequence != i:
                return {"valid": False, "entries": len(chain), "failed_at": i, "message": f"Chain break at sequence {i}"}
            prev_hash = entry.entry_hash

        if self.last_hashes.get(case_id) != prev_hash:
            return {"valid": False, "entries": len(chain), "message": "Last hash does not match"}
        return {"valid": True, "entries": len(chain), "message": "Chain integrity verified"}

    def get_audit_log(self, case_id: str, limit: int = 100) -> List[dict]:
        chain = self.chains.get(case_id, [])
        if limit <= 0:
            return []
        entries = []
        for entry in chain[-limit:]:
            entries.append({
                "sequence": entry.sequence,
                "event_type": entry.event_type,
                "case_id": entry.case_id,
                "details": entry.details,
                "timestamp": entry.timestamp,
                "hash": entry.entry_hash[:16] + "...",
            })
        return entries

    def get_trail_summary(self) -> dict:
        total_entries = sum(len(chain) for chain in self.chains.values())
        return {
            "total_cases": len(self.chains),
            "total_entries": total_entries,
            "cases_tracked": list(self.chains.keys()),
        }
