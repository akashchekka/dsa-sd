import time
from threading import Lock

from interfaces.rate_limiter import RateLimiter
from models.sliding_window import SlidingWindow


class SlidingWindowRateLimiter(RateLimiter):

    def __init__(self, limit: int, window_size_seconds: int):
        self.limit = limit
        self.window_size_seconds = window_size_seconds
        self.windows = {}
        self.windows_lock = Lock()

    def _get_window(self, user_id: str) -> SlidingWindow:
        window = self.windows.get(user_id)

        if window is not None:
            return window

        with self.windows_lock:
            window = self.windows.get(user_id)

            if window is None:
                window = SlidingWindow()
                self.windows[user_id] = window

            return window

    def allow_request(self, user_id: str) -> bool:
        window = self._get_window(user_id)

        with window.lock:
            now = time.monotonic()

            while (
                window.timestamps and
                now - window.timestamps[0] > self.window_size_seconds
            ):
                window.timestamps.popleft()

            if len(window.timestamps) >= self.limit:
                return False

            window.timestamps.append(now)
            return True
