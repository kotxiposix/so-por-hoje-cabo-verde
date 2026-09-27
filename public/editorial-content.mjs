import { normalizeEditorialLink } from "./editorial-links.mjs";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const KINDS = new Set(["podcast", "video", "story", "resource", "exhibition", "event"]);

function normalizeText(value, maxLength, required = false) {
  if (value === null || value === undefined) return required ? null : "";
  if (typeof value !== "string") return null;
  const cleaned = value.trim().replace(/\s+/g, " ");
  if ((required && !cleaned) || cleaned.length > maxLength) return null;
  return cleaned;
}

function normalizeSameOriginImage(value, origin) {
  const cleaned = normalizeText(value, 500);
  if (cleaned === null || !cleaned) return "";
  try {
    const base = new URL(origin);
    const url = new URL(cleaned, base);
    if (url.origin !== base.origin || url.username || url.password) return "";
    return url.href;
  } catch {
    return "";
  }
}

export function normalizePublishedEditorialItem(value, origin) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const id = normalizeText(value.id, 36, true)?.toLowerCase() || "";
  const kind = normalizeText(value.kind, 30, true);
  const title = normalizeText(value.title, 160, true);
  const summary = normalizeText(value.summary, 600, true);
  const rawUrl = normalizeText(value.url, 500, true);
  const displayDate = normalizeText(value.display_date, 80);
  const destination = rawUrl ? normalizeEditorialLink(rawUrl, origin) : null;

  if (
    !UUID_PATTERN.test(id)
    || !KINDS.has(kind)
    || !title
    || !summary
    || !destination
    || displayDate === null
  ) return null;

  return {
    id,
    kind,
    title,
    summary,
    url: destination.href,
    image_url: normalizeSameOriginImage(value.image_url, origin),
    display_date: displayDate,
  };
}

export function normalizePublishedEditorialItems(value, origin, limit = 50) {
  if (!Array.isArray(value)) return [];
  const safeLimit = Math.max(1, Math.min(Number.isInteger(limit) ? limit : 50, 100));
  const items = [];
  const seen = new Set();

  for (const valueItem of value) {
    const item = normalizePublishedEditorialItem(valueItem, origin);
    if (!item || seen.has(item.id)) continue;
    seen.add(item.id);
    items.push(item);
    if (items.length >= safeLimit) break;
  }
  return items;
}
