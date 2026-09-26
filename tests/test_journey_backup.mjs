import assert from "node:assert/strict";
import test from "node:test";

import {
  JOURNEY_BACKUP_VERSION,
  MAX_JOURNEY_BACKUP_BYTES,
  parseJourneyBackup,
} from "../public/journey-backup.mjs";

test("accepts the current version and returns only the journey payload", () => {
  const progress = { completed: ["2026-09-26"], checkins: { "2026-09-26": "firme" } };
  const result = parseJourneyBackup(JSON.stringify({ version: JOURNEY_BACKUP_VERSION, progress }));

  assert.deepEqual(result, progress);
});

test("rejects unknown versions, arrays and oversized backups", () => {
  assert.throws(() => parseJourneyBackup(JSON.stringify({ version: 2, progress: {} })), /Versão/);
  assert.throws(() => parseJourneyBackup(JSON.stringify({ version: 1, progress: [] })), /Jornada/);
  assert.throws(
    () => parseJourneyBackup(`{"version":1,"progress":{"value":"${"x".repeat(MAX_JOURNEY_BACKUP_BYTES)}"}}`),
    /limite/,
  );
});
