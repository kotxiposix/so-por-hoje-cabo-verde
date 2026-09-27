from __future__ import annotations

import os
from hmac import compare_digest
from typing import Mapping
from urllib.parse import urlsplit


def normalize_https_origin(value: object) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = value.strip()
    if not cleaned or any(character.isspace() or ord(character) < 32 for character in cleaned):
        return ""
    try:
        parsed = urlsplit(cleaned)
        _ = parsed.port
    except ValueError:
        return ""
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        return ""
    return f"https://{parsed.netloc.lower()}"


def is_safe_https_origin(value: object) -> bool:
    return bool(normalize_https_origin(value))


def is_bearer_secret(authorization: str | None, expected_secret: str) -> bool:
    if not authorization or not expected_secret:
        return False
    scheme, separator, token = authorization.partition(" ")
    return bool(
        separator
        and scheme.lower() == "bearer"
        and token
        and compare_digest(token, expected_secret)
    )


def admin_access_allowed(
    authorization: str | None,
    environment: Mapping[str, str] | None = None,
) -> bool:
    env = environment if environment is not None else os.environ
    return is_bearer_secret(authorization, env.get("ADMIN_API_SECRET", "").strip())
