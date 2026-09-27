import assert from "node:assert/strict";
import test from "node:test";

import {
  DEVICE_ONLY_PROGRESS_FIELDS,
  JOURNEY_SCHEMA_VERSION,
  SYNCABLE_PROGRESS_FIELDS,
  hasRemoteJourneyConflict,
  mergeRemoteJourneyProgress,
  selectSyncableProgress,
  validateRemoteJourneyRecord,
} from "../public/journey-sync.mjs";

test("keeps device-only fields out of journey synchronization", () => {
  const syncable = selectSyncableProgress({
    completed: ["2026-09-26"],
    supportPlan: { safePerson: "Pessoa segura" },
    anonymousName: "Guerreiro123",
    anonymousShares: [{ message: "Partilha local" }],
    notifications: "on",
    lastReminderAt: "2026-09-26",
    reminderTime: "08:30",
    showCleanDays: false,
    unexpectedFutureField: "não sincronizar",
  });

  assert.deepEqual(syncable, {
    completed: ["2026-09-26"],
    supportPlan: { safePerson: "Pessoa segura" },
  });
});

test("uses an explicit allowlist for synchronized journey data", () => {
  assert.deepEqual(SYNCABLE_PROGRESS_FIELDS, [
    "completed",
    "sobrietyDate",
    "checkins",
    "gratitudes",
    "supportPlan",
    "updatedAt",
  ]);
});

test("keeps the device-only contract explicit and preserves it over remote data", () => {
  assert.deepEqual(DEVICE_ONLY_PROGRESS_FIELDS, [
    "anonymousName",
    "anonymousShares",
    "notifications",
    "lastReminderAt",
    "reminderTime",
    "showCleanDays",
  ]);

  const merged = mergeRemoteJourneyProgress(
    {
      completed: ["2026-09-27"],
      reminderTime: "05:00",
      showCleanDays: true,
      anonymousName: "Nome remoto",
    },
    {
      reminderTime: "08:30",
      showCleanDays: false,
      anonymousName: "Nome local",
    },
  );

  assert.deepEqual(merged, {
    completed: ["2026-09-27"],
    reminderTime: "08:30",
    showCleanDays: false,
    anonymousName: "Nome local",
  });
});

test("accepts supported remote journey records", () => {
  const payload = { completed: ["2026-09-26"] };
  const record = validateRemoteJourneyRecord({
    payload,
    schema_version: JOURNEY_SCHEMA_VERSION,
    updated_at: "2026-09-26T10:00:00Z",
  });

  assert.deepEqual(record.payload, payload);
  assert.equal(record.schemaVersion, JOURNEY_SCHEMA_VERSION);
  assert.equal(record.updatedAt, "2026-09-26T10:00:00.000Z");
});

test("rejects future, malformed and undated remote records", () => {
  assert.throws(() => validateRemoteJourneyRecord({
    payload: {},
    schema_version: JOURNEY_SCHEMA_VERSION + 1,
    updated_at: "2026-09-26T10:00:00Z",
  }), /versão mais recente/);
  assert.throws(() => validateRemoteJourneyRecord({
    payload: [],
    schema_version: JOURNEY_SCHEMA_VERSION,
    updated_at: "2026-09-26T10:00:00Z",
  }), /Jornada válida/);
  assert.throws(() => validateRemoteJourneyRecord({
    payload: {},
    schema_version: JOURNEY_SCHEMA_VERSION,
    updated_at: "sem-data",
  }), /data de atualização/);
});

test("pauses automatic sync when the remote copy is newer", () => {
  assert.equal(hasRemoteJourneyConflict("2026-09-26T09:00:00Z", "2026-09-26T10:00:00Z"), true);
  assert.equal(hasRemoteJourneyConflict("2026-09-26T11:00:00Z", "2026-09-26T10:00:00Z"), false);
  assert.equal(hasRemoteJourneyConflict("", "2026-09-26T10:00:00Z"), true);
});
