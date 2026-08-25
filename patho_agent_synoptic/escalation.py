"""
Automated Escalation Protocol for Patho Agent Synoptic.
Rule-based escalation engine with role-appropriate notifications and response time tracking.
"""
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class EscalationTier(str, Enum):
    TIER_1_TECH = "TIER_1_TECH"
    TIER_2_PATHOLOGIST = "TIER_2_PATHOLOGIST"
    TIER_3_LAB_DIRECTOR = "TIER_3_LAB_DIRECTOR"
    TIER_4_CHIEF_MEDICAL_OFFICER = "TIER_4_CHIEF_MEDICAL_OFFICER"


@dataclass
class EscalationRule:
    """Defines when and how to escalate an alert."""
    rule_id: str
    condition: str  # e.g., "stat_critical", "unacknowledged_15min", "repeat_alert"
    target_tier: EscalationTier
    timeout_minutes: int
    notification_method: str  # "pager", "email", "sms", "webhook"
    auto_escalate: bool = True


@dataclass
class EscalationEvent:
    """Record of an escalation event."""
    event_id: str
    case_id: str
    alert_id: str
    tier: EscalationTier
    triggered_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    response_time_minutes: Optional[float] = None

    def acknowledge(self, user_id: str):
        self.acknowledged_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.acknowledged_by = user_id
        triggered = datetime.datetime.fromisoformat(self.triggered_at)
        acked = datetime.datetime.fromisoformat(self.acknowledged_at)
        self.response_time_minutes = round((acked - triggered).total_seconds() / 60, 1)


class EscalationEngine:
    """Rule-based escalation engine with tiered notifications."""

    DEFAULT_RULES = [
        EscalationRule("R1", "stat_critical", EscalationTier.TIER_2_PATHOLOGIST, 5, "pager"),
        EscalationRule("R2", "unacknowledged_15min", EscalationTier.TIER_3_LAB_DIRECTOR, 15, "email"),
        EscalationRule("R3", "unacknowledged_30min", EscalationTier.TIER_4_CHIEF_MEDICAL_OFFICER, 30, "sms"),
        EscalationRule("R4", "repeat_alert_3x", EscalationTier.TIER_3_LAB_DIRECTOR, 0, "email"),
    ]

    def __init__(self):
        self.rules: List[EscalationRule] = list(self.DEFAULT_RULES)
        self.events: List[EscalationEvent] = []
        self.pending: Dict[str, EscalationEvent] = {}

    def evaluate_alert(self, case_id: str, alert_id: str, urgency: str, repeat_count: int = 1) -> Optional[EscalationEvent]:
        rule = None
        if urgency == "STAT_CRITICAL":
            rule = next((r for r in self.rules if r.condition == "stat_critical"), None)
        elif repeat_count >= 3:
            rule = next((r for r in self.rules if r.condition == "repeat_alert_3x"), None)

        if not rule:
            return None

        event = EscalationEvent(
            event_id=f"ESC-{len(self.events) + 1:04d}",
            case_id=case_id,
            alert_id=alert_id,
            tier=rule.target_tier,
        )
        self.events.append(event)
        self.pending[event.event_id] = event
        return event

    def acknowledge_escalation(self, event_id: str, user_id: str) -> Optional[EscalationEvent]:
        event = self.pending.pop(event_id, None)
        if event:
            event.acknowledge(user_id)
        return event

    def check_timeouts(self) -> List[EscalationEvent]:
        now = datetime.datetime.now(datetime.timezone.utc)
        overdue = []
        for event_id, event in list(self.pending.items()):
            triggered = datetime.datetime.fromisoformat(event.triggered_at)
            elapsed = (now - triggered).total_seconds() / 60
            if elapsed > 15 and event.tier.value < EscalationTier.TIER_4_CHIEF_MEDICAL_OFFICER.value:
                overdue.append(event)
        return overdue

    def get_escalation_stats(self) -> dict:
        if not self.events:
            return {"total_events": 0, "mean_response_time_min": 0, "acknowledgment_rate": 0}
        acked = [e for e in self.events if e.acknowledged_at]
        response_times = [e.response_time_minutes for e in acked if e.response_time_minutes is not None]
        return {
            "total_events": len(self.events),
            "acknowledged": len(acked),
            "pending": len(self.pending),
            "acknowledgment_rate": round(len(acked) / len(self.events) * 100, 1),
            "mean_response_time_min": round(sum(response_times) / len(response_times), 1) if response_times else 0,
        }
