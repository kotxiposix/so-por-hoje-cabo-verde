const SUPPORT_FIELDS = ["activity", "phrase", "mental_challenge", "safety_note"];
const SUPPORT_STATES = new Set(["standard", "ansioso", "risco", "consumo"]);

function isSupportEntry(entry) {
  return entry
    && typeof entry === "object"
    && /^\d{2}-\d{2}$/.test(entry.month_day)
    && SUPPORT_STATES.has(entry.state)
    && SUPPORT_FIELDS.every((field) => typeof entry[field] === "string" && entry[field].trim());
}

export function selectDailySupport(catalog, monthDay, requestedState = "standard") {
  if (!Array.isArray(catalog) || !/^\d{2}-\d{2}$/.test(monthDay)) return null;
  const state = SUPPORT_STATES.has(requestedState) ? requestedState : "standard";
  const matches = catalog.filter((entry) => isSupportEntry(entry) && entry.month_day === monthDay);
  const selected = matches.find((entry) => entry.state === state)
    || matches.find((entry) => entry.state === "standard");
  if (!selected) return null;
  return Object.fromEntries(SUPPORT_FIELDS.map((field) => [field, selected[field].trim()]));
}
