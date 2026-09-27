import assert from "node:assert/strict";
import test from "node:test";

import {
  addIsoDays,
  differenceInCalendarDays,
  getBestStreak,
  getCurrentStreak,
} from "../public/date-utils.mjs";

test("date arithmetic crosses months and leap day in UTC", () => {
  assert.equal(addIsoDays("2026-03-01", -1), "2026-02-28");
  assert.equal(addIsoDays("2024-03-01", -1), "2024-02-29");
  assert.equal(addIsoDays("2026-12-31", 1), "2027-01-01");
  assert.equal(differenceInCalendarDays("2024-02-28", "2024-03-01"), 2);
});

test("current streak follows consecutive date-only values", () => {
  const completed = new Set(["2024-02-28", "2024-02-29", "2024-03-01"]);

  assert.equal(getCurrentStreak(completed, "2024-03-01"), 3);
  assert.equal(getCurrentStreak(completed, "2024-03-02"), 0);
});

test("best streak ignores duplicates and separates gaps", () => {
  assert.equal(
    getBestStreak(["2026-01-04", "2026-01-01", "2026-01-02", "2026-01-02"]),
    2,
  );
});

test("invalid calendar dates are rejected", () => {
  assert.throws(() => addIsoDays("2026-02-30", 1), /inválida/);
  assert.throws(() => differenceInCalendarDays("not-a-date", "2026-01-01"), /inválida/);
});
