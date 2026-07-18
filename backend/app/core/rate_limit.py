"""
In-memory login rate limiter for demonstration.

NOT suitable for multi-instance production deployments.
Use Redis or a distributed cache for production.
"""
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Optional

MAX_ATTEMPTS = 5
WINDOW_MINUTES = 15
COOLDOWN_MINUTES = 15


class LoginRateLimiter:
    def __init__(self):
        self._state: dict[str, tuple[int, datetime]] = {}
        self._lock = Lock()

    def _make_key(self, email: str, ip: str) -> str:
        return f"{email.lower().strip()}|{ip}"

    def check_rate_limit(self, email: str, ip: str) -> tuple[bool, Optional[int]]:
        key = self._make_key(email, ip)
        with self._lock:
            if key not in self._state:
                return False, None

            count, first_at = self._state[key]
            now = datetime.now(timezone.utc)
            elapsed_minutes = (now - first_at).total_seconds() / 60

            if elapsed_minutes >= WINDOW_MINUTES:
                del self._state[key]
                return False, None

            if count >= MAX_ATTEMPTS:
                cooldown_remaining = COOLDOWN_MINUTES - elapsed_minutes
                retry_after = int(cooldown_remaining * 60)
                if retry_after < 1:
                    retry_after = 1
                return True, retry_after

            return False, None

    def record_failure(self, email: str, ip: str) -> None:
        key = self._make_key(email, ip)
        with self._lock:
            if key in self._state:
                count, first_at = self._state[key]
                self._state[key] = (count + 1, first_at)
            else:
                self._state[key] = (1, datetime.now(timezone.utc))

    def clear_failures(self, email: str, ip: str) -> None:
        key = self._make_key(email, ip)
        with self._lock:
            if key in self._state:
                del self._state[key]

    def reset(self) -> None:
        with self._lock:
            self._state.clear()


login_rate_limiter = LoginRateLimiter()