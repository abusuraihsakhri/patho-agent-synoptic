"use strict";
const assert = require("node:assert/strict");
const { assess } = require("./app.js");

const base = {
  task_id: "T-1", target_identifier: "SYNTH-1",
  primary_metric: 10, secondary_metric: 5,
  status_descriptor: "NORMAL", is_critical_flag: false
};
const run = changes => assess(Object.assign({}, base, changes));

assert.equal(run({}).total_alerts, 0);
assert.equal(run({}).overall_urgency, "ROUTINE");
assert.equal(run({ primary_metric: 25 }).total_alerts, 0);
assert.equal(run({ primary_metric: 25.1 }).total_alerts, 1);
assert.equal(run({ secondary_metric: 12 }).total_alerts, 0);
assert.equal(run({ secondary_metric: 12.1 }).total_alerts, 1);
assert.equal(run({ status_descriptor: "discordant finding" }).total_alerts, 1);
assert.equal(run({ status_descriptor: "MUTANT" }).total_alerts, 1);
assert.equal(run({ is_critical_flag: true }).overall_urgency, "CRITICAL_STAT_PANIC");
assert.equal(run({ primary_metric: 30, secondary_metric: 13, status_descriptor: "FAIL",
  is_critical_flag: true }).total_alerts, 3);
assert.equal(run({}).audit_hash, null);
assert.throws(() => run({ primary_metric: "NaN" }), /finite numbers/);
assert.throws(() => run({ secondary_metric: "Infinity" }), /finite numbers/);
assert.throws(() => run({ target_identifier: "" }), /required/);
assert.throws(() => run({ task_id: "<x>".repeat(40) }), /length/);
console.log("Browser rule and validation checks passed.");
