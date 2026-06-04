import time
from threading import Lock

from interfaces.rate_limiter import RateLimiter
from models.leaky_bucket import LeakyBucket


class LeakyBucketRateLimiter(RateLimiter):

    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.buckets = {}
        self.buckets_lock = Lock()

    def _get_bucket(self, user_id: str) -> LeakyBucket:
        bucket = self.buckets.get(user_id)

        if bucket is not None:
            return bucket

        with self.buckets_lock:
            bucket = self.buckets.get(user_id)

            if bucket is None:
                bucket = LeakyBucket()
                self.buckets[user_id] = bucket

            return bucket

    def allow_request(self, user_id: str) -> bool:
        bucket = self._get_bucket(user_id)

        with bucket.lock:
            now = time.monotonic()
            elapsed = now - bucket.last_leak_time

            bucket.water = max(
                0.0,
                bucket.water - elapsed * self.leak_rate,
            )
            bucket.last_leak_time = now

            if bucket.water + 1 <= self.capacity:
                bucket.water += 1
                return True

            return False
