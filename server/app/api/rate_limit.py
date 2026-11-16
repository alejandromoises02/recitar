"""How many requests one caller may make to the public endpoints that count things (/go, /track).

Counts live in this process's memory, per fixed window: they are lost on restart and each server instance
keeps its own, which is enough to stop one caller from inflating the numbers. The caller is the client
address the server sees; behind a proxy, the server must be started so that this address is the visitor's
(uvicorn --forwarded-allow-ips with the proxy's own addresses), or every visitor shares the proxy's limit.
Never '*': uvicorn then takes the first X-Forwarded-For entry, which the caller writes, and anyone can
dodge the limit.
"""

import math
import threading
import time
from typing import Callable

from fastapi import Request

from app.api.problems import TooManyRequestsError

# per caller and minute; a person browsing never gets near either
TRACK_PER_MINUTE = 120
GO_PER_MINUTE = 30
# callers remembered per window; past it, new callers are refused until the window ends (a flood of addresses)
MAX_CALLERS = 100_000


class RateLimiter:
    def __init__(
        self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic, max_callers: int = MAX_CALLERS
    ):
        if limit < 1 or window_seconds <= 0:
            raise ValueError("a limit lets at least one request through in a window longer than zero")
        self._limit, self._window, self._clock, self._max_callers = limit, window_seconds, clock, max_callers
        self._lock = threading.Lock()  # sync endpoints run on several threads at once
        self._window_index: int | None = None
        self._counts: dict[str, int] = {}

    def allow(self, caller: str) -> bool:
        """Counts one request from `caller` and says whether it is within the limit."""
        with self._lock:
            index = math.floor(self._clock() / self._window)
            if index != self._window_index:
                self._window_index, self._counts = index, {}
            count = self._counts.get(caller)
            if count is None:
                if len(self._counts) >= self._max_callers:
                    return False
                count = 0
            if count >= self._limit:
                return False
            self._counts[caller] = count + 1
            return True

    def retry_after(self) -> int:
        """Whole seconds until the current window ends."""
        now = self._clock()
        end = (math.floor(now / self._window) + 1) * self._window
        return max(1, math.ceil(end - now))

    def reset(self) -> None:
        with self._lock:
            self._window_index, self._counts = None, {}


def default_rate_limits() -> dict[str, RateLimiter]:
    return {"track": RateLimiter(TRACK_PER_MINUTE, 60), "go": RateLimiter(GO_PER_MINUTE, 60)}


def _caller(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


def _limiter(request: Request, name: str) -> RateLimiter | None:
    return request.app.state.rate_limits.get(name)


def limit_track(request: Request) -> None:
    """Refuses (429) a caller that sent too many events this minute."""
    limiter = _limiter(request, "track")
    if limiter is not None and not limiter.allow(_caller(request)):
        raise TooManyRequestsError(limiter.retry_after())


def go_click_counts(request: Request) -> bool:
    """Whether this ticket click may still be counted. Over the limit the visitor is still sent to the
    tickets, since many people can share one address (mobile carriers); only the count stops."""
    limiter = _limiter(request, "go")
    return limiter is None or limiter.allow(_caller(request))
