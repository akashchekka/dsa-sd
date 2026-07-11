from enums.rate_limiter_type import RateLimiterType
from strategies.token_bucket_rate_limiter import TokenBucketRateLimiter
from strategies.leaky_bucket_rate_limiter import LeakyBucketRateLimiter
from strategies.fixed_window_rate_limiter import FixedWindowRateLimiter
from strategies.sliding_window_rate_limiter import SlidingWindowRateLimiter


class RateLimiterFactory:

    @staticmethod
    def create(rate_limiter_type, **kwargs):

        if rate_limiter_type == RateLimiterType.TOKEN_BUCKET:
            return TokenBucketRateLimiter(**kwargs)

        if rate_limiter_type == RateLimiterType.LEAKY_BUCKET:
            return LeakyBucketRateLimiter(**kwargs)

        if rate_limiter_type == RateLimiterType.FIXED_WINDOW:
            return FixedWindowRateLimiter(**kwargs)

        if rate_limiter_type == RateLimiterType.SLIDING_WINDOW:
            return SlidingWindowRateLimiter(**kwargs)

        raise ValueError("Unsupported type")
