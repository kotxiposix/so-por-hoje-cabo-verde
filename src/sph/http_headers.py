from __future__ import annotations


CONTENT_SECURITY_POLICY = (
    "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
    "script-src 'self' https://challenges.cloudflare.com; style-src 'self'; img-src 'self' data: blob:; font-src 'self'; "
    "connect-src 'self' https://*.supabase.co; "
    "frame-src https://www.youtube-nocookie.com https://challenges.cloudflare.com; worker-src 'self'; manifest-src 'self'; "
    "form-action 'self' mailto:"
)
SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}
NO_STORE = "private, no-store"
REVALIDATE = "public, max-age=0, must-revalidate"
