function normalizePhone(value) {
  const match = String(value || "").match(/\+?\d[\d\s-]{5,}/);
  if (!match) return "";
  const normalized = match[0].replace(/(?!^)\D/g, "");
  const digits = normalized.replace(/\D/g, "");
  return digits.length >= 6 && digits.length <= 15 ? normalized : "";
}

export function normalizeHelpAction(kind, value) {
  if (typeof value !== "string" || !value.trim()) return null;
  const cleaned = value.trim();

  if (kind === "phone") {
    const phone = normalizePhone(cleaned);
    return phone ? { href: `tel:${phone}`, external: false } : null;
  }

  if (kind === "email") {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleaned)) return null;
    return { href: `mailto:${cleaned}`, external: false };
  }

  if (kind === "web") {
    try {
      const url = new URL(cleaned);
      if (url.protocol !== "https:" || url.username || url.password) return null;
      return { href: url.href, external: true };
    } catch {
      return null;
    }
  }

  return null;
}
