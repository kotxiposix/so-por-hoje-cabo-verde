import assert from "node:assert/strict";
import test from "node:test";

import { createSafeStorage } from "../public/safe-storage.mjs";

function memoryStorage() {
  const values = new Map();
  return {
    get length() { return values.size; },
    getItem: (key) => values.has(key) ? values.get(key) : null,
    key: (index) => [...values.keys()][index] ?? null,
    removeItem: (key) => values.delete(key),
    setItem: (key, value) => values.set(key, String(value)),
  };
}

test("safe storage preserves the Storage contract when available", () => {
  const backend = memoryStorage();
  const storage = createSafeStorage(() => backend);

  assert.equal(storage.setItem("sph-progress", "{}"), true);
  assert.equal(storage.getItem("sph-progress"), "{}");
  assert.deepEqual(storage.keys(), ["sph-progress"]);
  assert.equal(storage.removeItem("sph-progress"), true);
  assert.equal(storage.getItem("sph-progress"), null);
});

test("safe storage contains provider and quota failures", () => {
  let unavailable = 0;
  const blocked = createSafeStorage(() => {
    throw new Error("blocked");
  }, () => { unavailable += 1; });

  assert.equal(blocked.getItem("key"), null);
  assert.equal(blocked.setItem("key", "value"), false);
  assert.equal(blocked.removeItem("key"), false);
  assert.deepEqual(blocked.keys(), []);
  assert.equal(unavailable, 4);

  const quota = createSafeStorage(() => ({
    get length() { return 0; },
    getItem: () => null,
    key: () => null,
    removeItem: () => {},
    setItem: () => { throw new Error("quota"); },
  }), () => { unavailable += 1; });
  assert.equal(quota.setItem("key", "value"), false);
  assert.equal(unavailable, 5);
});
