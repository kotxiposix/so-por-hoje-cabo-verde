import assert from "node:assert/strict";
import test from "node:test";

import {
  createJourneyBackup,
  JOURNEY_BACKUP_VERSION,
  MAX_JOURNEY_BACKUP_BYTES,
  mergeJourneyBackupProgress,
  parseJourneyBackup,
} from "../public/journey-backup.mjs";

test("exports only portable journey fields", () => {
  const backup = createJourneyBackup({
    completed: ["2026-09-26"],
    gratitudes: { "2026-09-26": "Hoje" },
    anonymousName: "Guerreiro123",
    anonymousShares: [{ message: "Local" }],
    notifications: "on",
    reminderTime: "08:30",
    showCleanDays: false,
  }, "2026-09-27T10:00:00Z");

  assert.deepEqual(backup, {
    exportedAt: "2026-09-27T10:00:00Z",
    version: JOURNEY_BACKUP_VERSION,
    progress: {
      completed: ["2026-09-26"],
      gratitudes: { "2026-09-26": "Hoje" },
    },
  });
});

test("keeps device-only values when applying an imported journey", () => {
  const merged = mergeJourneyBackupProgress(
    {
      completed: ["2026-09-26"],
      anonymousName: "Nome da cópia antiga",
      reminderTime: "05:00",
    },
    {
      anonymousName: "Nome deste dispositivo",
      anonymousShares: [{ message: "Mantém-me local" }],
      reminderTime: "08:30",
      showCleanDays: false,
    },
  );

  assert.deepEqual(merged, {
    completed: ["2026-09-26"],
    anonymousName: "Nome deste dispositivo",
    anonymousShares: [{ message: "Mantém-me local" }],
    reminderTime: "08:30",
    showCleanDays: false,
  });
});

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
