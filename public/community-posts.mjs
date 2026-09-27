const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const PSEUDONYM_PATTERN = /^Guerreiro\d{4}$/;
const TIMEZONE_PATTERN = /(?:Z|[+-]\d{2}:\d{2})$/i;

function normalizeBody(value) {
  if (typeof value !== "string") return "";
  const body = value.trim().replace(/\s+/g, " ");
  return body && body.length <= 280 ? body : "";
}

export function normalizePublishedCommunityPost(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const id = typeof value.id === "string" ? value.id.trim().toLowerCase() : "";
  const pseudonym = typeof value.pseudonym === "string" ? value.pseudonym.trim() : "";
  const body = normalizeBody(value.body);
  const createdAt = typeof value.created_at === "string" ? value.created_at.trim() : "";
  const timestamp = Date.parse(createdAt);

  if (!UUID_PATTERN.test(id) || !PSEUDONYM_PATTERN.test(pseudonym) || !body) return null;
  if (!TIMEZONE_PATTERN.test(createdAt) || !Number.isFinite(timestamp)) return null;

  return {
    id,
    pseudonym,
    body,
    created_at: new Date(timestamp).toISOString(),
  };
}

export function normalizePublishedCommunityPosts(value, limit = 20) {
  if (!Array.isArray(value)) return [];
  const safeLimit = Math.max(1, Math.min(Number.isInteger(limit) ? limit : 20, 50));
  const seen = new Set();
  const posts = [];

  for (const item of value) {
    const post = normalizePublishedCommunityPost(item);
    if (!post || seen.has(post.id)) continue;
    seen.add(post.id);
    posts.push(post);
    if (posts.length >= safeLimit) break;
  }
  return posts;
}
