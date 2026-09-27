const BASE64URL_PATTERN = /^[A-Za-z0-9_-]+={0,2}$/;

function isPrivateEndpointHost(hostname) {
  const host = hostname.toLowerCase().replace(/^\[|\]$/g, "");
  if (host === "localhost" || host.endsWith(".localhost") || host.endsWith(".local") || host.endsWith(".internal")) {
    return true;
  }
  if (host === "::1" || host.startsWith("fc") || host.startsWith("fd") || host.startsWith("fe80:")) {
    return true;
  }
  const octets = host.split(".").map(Number);
  if (octets.length !== 4 || octets.some((octet) => !Number.isInteger(octet) || octet < 0 || octet > 255)) {
    return false;
  }
  return octets[0] === 10
    || octets[0] === 127
    || (octets[0] === 169 && octets[1] === 254)
    || (octets[0] === 172 && octets[1] >= 16 && octets[1] <= 31)
    || (octets[0] === 192 && octets[1] === 168);
}

export function normalizePushEndpoint(value) {
  if (typeof value !== "string") return "";
  const cleaned = value.trim();
  if (!cleaned || cleaned.length > 2048) return "";
  try {
    const url = new URL(cleaned);
    if (
      url.protocol !== "https:"
      || url.username
      || url.password
      || isPrivateEndpointHost(url.hostname)
    ) return "";
    return url.href;
  } catch {
    return "";
  }
}

function normalizePushKey(value, minimum, maximum) {
  if (typeof value !== "string") return "";
  const cleaned = value.trim();
  if (
    cleaned.length < minimum
    || cleaned.length > maximum
    || !BASE64URL_PATTERN.test(cleaned)
  ) return "";
  return cleaned;
}

export function normalizePushSubscription(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const endpoint = normalizePushEndpoint(value.endpoint);
  const p256dh = normalizePushKey(value.keys?.p256dh, 16, 512);
  const auth = normalizePushKey(value.keys?.auth, 8, 256);
  return endpoint && p256dh && auth ? { endpoint, keys: { p256dh, auth } } : null;
}
