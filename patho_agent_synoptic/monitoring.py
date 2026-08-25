"""
Real-Time Monitoring Dashboard for Patho Agent Synoptic.
Live visualization of key performance indicators with automated alerting for threshold breaches.
"""
import datetime
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class KPIMetric:
    """Key Performance Indicator metric data point."""
    metric_name: str
    value: float
    unit: str
    threshold_low: Optional[float] = None
    threshold_high: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @property
    def is_breached(self) -> bool:
        if self.threshold_high is not None and self.value > self.threshold_high:
            return True
        if self.threshold_low is not None and self.value < self.threshold_low:
            return True
        return False


class MonitoringDashboard:
    """Real-time monitoring dashboard with KPI tracking and threshold alerting."""

    DEFAULT_THRESHOLDS = {
        "case_throughput_per_hour": {"low": 5, "high": None},
        "alert_rate_pct": {"low": None, "high": 20.0},
        "stat_critical_rate_pct": {"low": None, "high": 5.0},
        "mean_processing_time_sec": {"low": None, "high": 30.0},
        "concordance_rate_pct": {"low": 85.0, "high": None},
    }

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.alert_log: List[dict] = []
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)

    def record_metric(self, metric_name: str, value: float, unit: str = "") -> KPIMetric:
        thresholds = self.thresholds.get(metric_name, {})
        metric = KPIMetric(
            metric_name=metric_name,
            value=value,
            unit=unit,
            threshold_low=thresholds.get("low"),
            threshold_high=thresholds.get("high"),
        )
        self.metrics_history[metric_name].append(metric)
        if metric.is_breached:
            alert = {
                "metric": metric_name,
                "value": value,
                "threshold": metric.threshold_high or metric.threshold_low,
                "direction": "above" if metric.threshold_high and value > metric.threshold_high else "below",
                "timestamp": metric.timestamp,
            }
            self.alert_log.append(alert)
        return metric

    def get_dashboard_summary(self) -> dict:
        summary = {}
        for name, history in self.metrics_history.items():
            if not history:
                continue
            values = [m.value for m in history]
            summary[name] = {
                "current": values[-1],
                "mean": round(statistics.mean(values), 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
                "count": len(values),
                "breach_count": sum(1 for m in history if m.is_breached),
            }
        return {
            "kpis": summary,
            "active_alerts": len([a for a in self.alert_log if self._is_recent(a["timestamp"])]),
            "total_alerts": len(self.alert_log),
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    def get_alerts(self, limit: int = 50) -> List[dict]:
        return self.alert_log[-limit:]

    def configure_threshold(self, metric_name: str, low: Optional[float] = None, high: Optional[float] = None):
        self.thresholds[metric_name] = {"low": low, "high": high}

    def _is_recent(self, timestamp_str: str, minutes: int = 60) -> bool:
        try:
            ts = datetime.datetime.fromisoformat(timestamp_str)
            now = datetime.datetime.now(datetime.timezone.utc)
            return (now - ts).total_seconds() < minutes * 60
        except (ValueError, TypeError):
            return False
