const ISO_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const DAY_MS = 86_400_000;

function isoDateToUtc(isoDate) {
  if (!ISO_DATE_PATTERN.test(isoDate || "")) throw new RangeError("Data inválida");
  const [year, month, day] = isoDate.split("-").map(Number);
  const value = Date.UTC(year, month - 1, day);
  const parsed = new Date(value);
  if (
    parsed.getUTCFullYear() !== year
    || parsed.getUTCMonth() !== month - 1
    || parsed.getUTCDate() !== day
  ) {
    throw new RangeError("Data inválida");
  }
  return value;
}

export function addIsoDays(isoDate, offset) {
  return new Date(isoDateToUtc(isoDate) + Number(offset) * DAY_MS).toISOString().slice(0, 10);
}

export function differenceInCalendarDays(startIso, endIso) {
  return Math.round((isoDateToUtc(endIso) - isoDateToUtc(startIso)) / DAY_MS);
}

export function getCurrentStreak(completedDays, todayIso) {
  if (!todayIso) return 0;
  const completed = completedDays instanceof Set ? completedDays : new Set(completedDays);
  let count = 0;
  let cursor = todayIso;

  while (completed.has(cursor)) {
    count += 1;
    cursor = addIsoDays(cursor, -1);
  }
  return count;
}

export function getBestStreak(completedDays) {
  const days = [...new Set(completedDays)].sort();
  let best = 0;
  let current = 0;
  let previous = "";

  for (const day of days) {
    current = previous && differenceInCalendarDays(previous, day) === 1 ? current + 1 : 1;
    best = Math.max(best, current);
    previous = day;
  }
  return best;
}
