from __future__ import annotations

import os
from hmac import compare_digest
from typing import Mapping


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
