import time
from threading import Lock


class LeakyBucket:

    def __init__(self):
        self.water = 0.0
        self.last_leak_time = time.monotonic()
        self.lock = Lock()
