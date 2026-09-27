export function normalizeEditorialLink(value, origin) {
  if (typeof value !== "string" || !value.trim()) return null;

  try {
    const base = new URL(origin);
    const url = new URL(value.trim(), base);
    const sameOrigin = url.origin === base.origin;
    if (!sameOrigin && url.protocol !== "https:") return null;
    if (url.username || url.password) return null;

    return {
      href: url.href,
      external: !sameOrigin,
    };
  } catch {
    return null;
  }
}
