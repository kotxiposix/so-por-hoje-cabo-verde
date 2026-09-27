import { normalizeHelpAction } from "./help-links.mjs";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const ISO_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const CATEGORIES = new Set([
  "emergency",
  "health",
  "treatment",
  "meeting",
  "family",
  "information",
  "other",
]);

function normalizeText(value, maxLength, required = false) {
  if (value === null || value === undefined) return required ? null : "";
  if (typeof value !== "string") return null;
  const cleaned = value.trim().replace(/\s+/g, " ");
  if ((required && !cleaned) || cleaned.length > maxLength) return null;
  return cleaned;
}

function normalizeContact(kind, value, maxLength) {
  const cleaned = normalizeText(value, maxLength);
  if (cleaned === null) return null;
  if (!cleaned) return "";
  return normalizeHelpAction(kind, cleaned) ? cleaned : null;
}

function isValidIsoDate(value) {
  if (!ISO_DATE_PATTERN.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  return parsed.getUTCFullYear() === year
    && parsed.getUTCMonth() === month - 1
    && parsed.getUTCDate() === day;
}

export function normalizePublishedHelpResource(value, todayIso) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  if (!isValidIsoDate(todayIso)) return null;

  const id = normalizeText(value.id, 36, true)?.toLowerCase() || "";
  const name = normalizeText(value.name, 120, true);
  const island = normalizeText(value.island, 60);
  const municipality = normalizeText(value.municipality, 80);
  const category = normalizeText(value.category, 40, true);
  const description = normalizeText(value.description, 1000, true);
  const phone = normalizeContact("phone", value.phone, 80);
  const email = normalizeContact("email", value.email, 254);
  const website = normalizeContact("web", value.website, 500);
  const sourceUrl = normalizeContact("web", value.source_url, 500);
  const verifiedAt = normalizeText(value.verified_at, 40);
  const reviewDueAt = normalizeText(value.review_due_at, 10, true);

  if (
    !UUID_PATTERN.test(id)
    || !name
    || !CATEGORIES.has(category)
    || !description
    || phone === null
    || email === null
    || website === null
    || !sourceUrl
    || verifiedAt === null
    || !reviewDueAt
    || !isValidIsoDate(reviewDueAt)
    || reviewDueAt < todayIso
    || typeof value.is_emergency !== "boolean"
  ) return null;

  if (!Array.isArray(value.schedule) || value.schedule.length > 20) return null;
  const schedule = value.schedule.map((item) => normalizeText(item, 120, true));
  if (schedule.some((item) => !item)) return null;
  if (value.is_emergency && !phone) return null;
  if (["meeting", "family"].includes(category)) {
    if (!schedule.length || !(phone || email || website)) return null;
  }

  return {
    id,
    name,
    island,
    municipality,
    category,
    description,
    phone,
    email,
    website,
    schedule,
    is_emergency: value.is_emergency,
    source_url: sourceUrl,
    verified_at: verifiedAt,
    review_due_at: reviewDueAt,
  };
}

export function normalizePublishedHelpResources(value, todayIso, limit = 100) {
  if (!Array.isArray(value) || !isValidIsoDate(todayIso)) return [];
  const safeLimit = Math.max(1, Math.min(Number.isInteger(limit) ? limit : 100, 200));
  const resources = [];
  const seen = new Set();

  for (const item of value) {
    const resource = normalizePublishedHelpResource(item, todayIso);
    if (!resource || seen.has(resource.id)) continue;
    seen.add(resource.id);
    resources.push(resource);
    if (resources.length >= safeLimit) break;
  }
  return resources;
}
