import time
from threading import Lock


class TokenBucket:

    def __init__(self, capacity: int):
        self.tokens = float(capacity)
        self.last_refill_time = time.monotonic()
        self.lock = Lock()
