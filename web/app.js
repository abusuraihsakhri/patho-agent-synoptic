(function (root) {
  "use strict";

  // Deliberately small, explicit client-side equivalent of agents/workers.py.
  // These numerical rules are software demonstration thresholds, not CAP criteria.
  function assess(input) {
    const taskId = String(input.task_id || "").trim();
    const target = String(input.target_identifier || "").trim();
    const status = String(input.status_descriptor || "").trim();
    const primary = Number(input.primary_metric);
    const secondary = Number(input.secondary_metric);
    if (!taskId || !target) throw new Error("Task ID and target identifier are required.");
    if (taskId.length > 120 || target.length > 120 || status.length > 300)
      throw new Error("Text input exceeds the supported length.");
    if (input.primary_metric === "" || input.secondary_metric === "" ||
        !Number.isFinite(primary) || !Number.isFinite(secondary))
      throw new Error("Both measurements must be finite numbers.");

    const alerts = [];
    if (primary > 25) {
      alerts.push({
        origin_worker: "InvariantQCWorker", urgency: "ELEVATED_RISK",
        summary: "Primary metric threshold exceeded",
        technical_details: "Measurement " + primary + " exceeds demonstration threshold 25.",
        actionable_remediation: "Review the measurement and its units."
      });
    }
    if (input.is_critical_flag === true || secondary > 12) {
      alerts.push({
        origin_worker: "SafetyEscalationWorker",
        urgency: input.is_critical_flag === true ? "CRITICAL_STAT_PANIC" : "ELEVATED_RISK",
        summary: "Priority flag or secondary metric threshold triggered",
        technical_details: "Critical flag: " + Boolean(input.is_critical_flag) + "; secondary: " + secondary + ".",
        actionable_remediation: "Review the flagged record under the local workflow."
      });
    }
    if (/DISCORDANT|ANOMALY|MUTANT|VIOLATION|FAIL|REJECT/.test(status.toUpperCase())) {
      alerts.push({
        origin_worker: "ProtocolConformanceWorker", urgency: "ELEVATED_RISK",
        summary: "Discordance keyword detected",
        technical_details: "Status descriptor contains a flagged term.",
        actionable_remediation: "Review the descriptor and supporting evidence."
      });
    }
    const critical = alerts.filter(a => a.urgency === "CRITICAL_STAT_PANIC").length;
    const elevated = alerts.filter(a => a.urgency === "ELEVATED_RISK").length;
    return {
      execution_mode: "BROWSER_LOCAL_DEMONSTRATION",
      task_id: taskId, target_identifier: target,
      overall_urgency: critical ? "CRITICAL_STAT_PANIC" : elevated ? "ELEVATED_RISK" : "ROUTINE",
      integrity_status: critical ? "RECALIBRATION_REQUIRED" :
        elevated ? "DISCORDANT_ANOMALY" : "VALIDATED_OPTIMAL",
      total_alerts: alerts.length, critical_alerts_count: critical, alerts,
      audit_hash: null,
      disclaimer: "Demonstration rules only. No CAP protocol validation, clinical verification, signed audit log, or server processing."
    };
  }

  if (typeof module !== "undefined" && module.exports) module.exports = { assess };
  if (!root.document) return;

  const doc = root.document;
  const form = doc.getElementById("audit-form");
  const output = doc.getElementById("output");
  const message = doc.getElementById("message");
  const download = doc.getElementById("download");
  const count = doc.getElementById("counter");
  let lastResult = null;
  let processed = 0;

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    message.textContent = "";
    try {
      const result = assess({
        task_id: doc.getElementById("task-id").value,
        target_identifier: doc.getElementById("target-id").value,
        primary_metric: doc.getElementById("primary").value,
        secondary_metric: doc.getElementById("secondary").value,
        status_descriptor: doc.getElementById("status").value,
        is_critical_flag: doc.getElementById("critical").checked
      });
      lastResult = result;
      processed += 1;
      count.textContent = String(processed);
      output.textContent = JSON.stringify(result, null, 2);
      download.disabled = false;
    } catch (error) {
      lastResult = null;
      download.disabled = true;
      output.textContent = "No result.";
      message.textContent = error.message;
    }
  });
  download.addEventListener("click", function () {
    if (!lastResult) return;
    const blob = new Blob([JSON.stringify(lastResult, null, 2) + "\n"], {type: "application/json"});
    const url = URL.createObjectURL(blob);
    const anchor = doc.createElement("a");
    anchor.href = url;
    anchor.download = "synoptic-demo-result.json";
    doc.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    root.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  });
})(typeof window !== "undefined" ? window : globalThis);
