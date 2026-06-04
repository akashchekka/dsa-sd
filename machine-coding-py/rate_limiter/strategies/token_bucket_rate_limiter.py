import time
from threading import Lock

from interfaces.rate_limiter import RateLimiter
from models.token_bucket import TokenBucket


class TokenBucketRateLimiter(RateLimiter):

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets = {}
        self.buckets_lock = Lock()

    def _get_bucket(self, user_id: str) -> TokenBucket:
        bucket = self.buckets.get(user_id)

        if bucket is not None:
            return bucket

        with self.buckets_lock:
            bucket = self.buckets.get(user_id)

            if bucket is None:
                bucket = TokenBucket(self.capacity)
                self.buckets[user_id] = bucket

            return bucket

    def allow_request(self, user_id: str) -> bool:
        bucket = self._get_bucket(user_id)

        with bucket.lock:
            now = time.monotonic()
            elapsed = now - bucket.last_refill_time

            bucket.tokens = min(
                float(self.capacity),
                bucket.tokens + elapsed * self.refill_rate,
            )
            bucket.last_refill_time = now

            if bucket.tokens >= 1:
                bucket.tokens -= 1
                return True

            return False
