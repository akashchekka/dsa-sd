import time

class SlidingWindowRateLimiter:
    def __init__(self, limit=100, window=60):
        self.limit = limit
        self.window = window

        self.previous_count = 0
        self.current_count = 0

        self.window_start = time.monotonic()

    def allow(self):
        now = time.monotonic()
        elapsed = now - self.window_start

        # Move to a new window
        if elapsed >= self.window:
            self.previous_count = self.current_count
            self.current_count = 0
            self.window_start = now
            elapsed = 0

        # How much of the previous window overlaps
        previous_weight = (self.window - elapsed) / self.window

        estimate = (
            self.current_count
            + self.previous_count * previous_weight
        )

        if estimate >= self.limit:
            return False

        self.current_count += 1
        return True