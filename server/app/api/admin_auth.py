"""The one admin: whoever holds ADMIN_TOKEN. Guards the few write endpoints (PUT /featured).

The token is a long random secret kept in the server environment, never in the repository. It is
sent as `Authorization: Bearer <token>` (over HTTPS in production) and compared in constant time.
Without a token of at least MIN_TOKEN_LENGTH characters configured, writing is off: a missing or
weak setting never leaves an endpoint open. Generate one with
`python -c "import secrets; print(secrets.token_urlsafe(32))"`.
"""

import hmac
import os
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.problems import AdminDisabledError, UnauthorizedError

MIN_TOKEN_LENGTH = 32

_bearer = HTTPBearer(auto_error=False, description="The admin token (ADMIN_TOKEN on the server)")


def require_admin(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> None:
    expected = os.environ.get("ADMIN_TOKEN", "").strip()  # read per request, so a change needs no restart
    if len(expected) < MIN_TOKEN_LENGTH:
        raise AdminDisabledError()
    given = credentials.credentials if credentials is not None else ""
    if not hmac.compare_digest(given.encode(), expected.encode()):
        raise UnauthorizedError()
