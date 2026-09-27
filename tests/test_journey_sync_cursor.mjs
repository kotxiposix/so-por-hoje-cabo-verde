import assert from "node:assert/strict";
import test from "node:test";

import {
  createJourneySyncCursor,
  readJourneySyncCursor,
  shouldPauseAutomaticSync,
} from "../public/journey-sync-cursor.mjs";

test("stores and restores a remote version only for the same account", () => {
  const cursor = createJourneySyncCursor("user-one", "2026-09-27T09:00:00Z");
  const serialized = JSON.stringify(cursor);

  assert.deepEqual(cursor, {
    userId: "user-one",
    updatedAt: "2026-09-27T09:00:00.000Z",
  });
  assert.equal(readJourneySyncCursor(serialized, "user-one"), "2026-09-27T09:00:00.000Z");
  assert.equal(readJourneySyncCursor(serialized, "user-two"), "");
  assert.equal(readJourneySyncCursor("not-json", "user-one"), "");
});

test("pauses automatic sync when a known remote copy changes or disappears", () => {
  const baseline = {
    knownRemoteUpdatedAt: "2026-09-27T09:00:00Z",
    remoteExists: true,
    remoteUpdatedAt: "2026-09-27T09:00:00Z",
    localUpdatedAt: "2026-09-27T09:30:00Z",
  };

  assert.equal(shouldPauseAutomaticSync(baseline), false);
  assert.equal(shouldPauseAutomaticSync({
    ...baseline,
    remoteUpdatedAt: "2026-09-27T10:00:00Z",
  }), true);
  assert.equal(shouldPauseAutomaticSync({ ...baseline, remoteExists: false }), true);
});

test("uses local recency only when no remote cursor exists yet", () => {
  assert.equal(shouldPauseAutomaticSync({
    knownRemoteUpdatedAt: "",
    remoteExists: false,
    remoteUpdatedAt: "",
    localUpdatedAt: "2026-09-27T09:00:00Z",
  }), false);
  assert.equal(shouldPauseAutomaticSync({
    knownRemoteUpdatedAt: "",
    remoteExists: true,
    remoteUpdatedAt: "2026-09-27T10:00:00Z",
    localUpdatedAt: "2026-09-27T09:00:00Z",
  }), true);
});
