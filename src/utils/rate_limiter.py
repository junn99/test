"""Rate limiter for API calls."""
import time
from threading import Lock
from collections import deque
from typing import Optional

from .logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, max_calls: int = 3, time_window: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in time window.
            time_window: Time window in seconds.
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
        self.lock = Lock()

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make an API call.

        Args:
            blocking: Whether to block until permission is granted.
            timeout: Maximum time to wait in seconds.

        Returns:
            True if permission granted, False otherwise.
        """
        start_time = time.time()

        while True:
            with self.lock:
                now = time.time()

                # Remove old calls outside time window
                while self.calls and now - self.calls[0] >= self.time_window:
                    self.calls.popleft()

                # Check if we can make a call
                if len(self.calls) < self.max_calls:
                    self.calls.append(now)
                    return True

            # If not blocking, return False immediately
            if not blocking:
                return False

            # Check timeout
            if timeout is not None and (time.time() - start_time) >= timeout:
                return False

            # Calculate wait time
            if self.calls:
                oldest_call = self.calls[0]
                wait_time = self.time_window - (time.time() - oldest_call)
                if wait_time > 0:
                    time.sleep(min(wait_time, 0.1))
            else:
                time.sleep(0.1)

    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


# Global rate limiter for Notion API (3 req/sec)
notion_rate_limiter = RateLimiter(max_calls=3, time_window=1.0)
