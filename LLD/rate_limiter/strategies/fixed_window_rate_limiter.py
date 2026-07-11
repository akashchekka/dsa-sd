import time
from threading import Lock

from interfaces.rate_limiter import RateLimiter
from models.fixed_window import FixedWindow


class FixedWindowRateLimiter(RateLimiter):

    def __init__(self, limit: int, window_size_seconds: int):
        self.limit = limit
        self.window_size_seconds = window_size_seconds
        self.windows = {}
        self.windows_lock = Lock()

    def _get_window(self, user_id: str) -> FixedWindow:
        window = self.windows.get(user_id)        # 1 lookup, atomic
        if window is not None:
            return window

        with self.windows_lock:
            window = self.windows.get(user_id)    # re-check under lock
            if window is None:
                window = FixedWindow()
                self.windows[user_id] = window
            return window

    def allow_request(self, user_id: str) -> bool:
        window = self._get_window(user_id)

        with window.lock:
            current_window = int(
                time.time() / self.window_size_seconds
            )

            if current_window != window.window_start: # Start of new Window 
                window.window_start = current_window
                window.request_count = 0

            if window.request_count >= self.limit:
                return False

            window.request_count += 1
            return True
