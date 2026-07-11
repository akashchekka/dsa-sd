from factories.rate_limiter_factory import RateLimiterFactory
from enums.rate_limiter_type import RateLimiterType


def demo(label, limiter, user, total_requests):
    print(f"\n--- {label} ---")
    allowed_count = 0
    blocked_count = 0

    for i in range(total_requests):
        if limiter.allow_request(user):
            allowed_count += 1
            verdict = "ALLOWED"
        else:
            blocked_count += 1
            verdict = "BLOCKED"
        print(f"Request {i + 1}: {verdict}")

    print(f"Summary: {allowed_count} allowed, {blocked_count} blocked")


def main():
    user = "user-123"

    token_bucket = RateLimiterFactory.create(
        RateLimiterType.TOKEN_BUCKET,
        capacity=10,
        refill_rate=2.0,
    )
    demo("Token Bucket (cap=10, refill=2/s)", token_bucket, user, 15)

    leaky_bucket = RateLimiterFactory.create(
        RateLimiterType.LEAKY_BUCKET,
        capacity=10,
        leak_rate=2.0,
    )
    demo("Leaky Bucket (cap=10, leak=2/s)", leaky_bucket, user, 15)

    fixed_window = RateLimiterFactory.create(
        RateLimiterType.FIXED_WINDOW,
        limit=10,
        window_size_seconds=60,
    )
    demo("Fixed Window (limit=10/60s)", fixed_window, user, 15)

    sliding_window = RateLimiterFactory.create(
        RateLimiterType.SLIDING_WINDOW,
        limit=10,
        window_size_seconds=60,
    )
    demo("Sliding Window Log (limit=10/60s)", sliding_window, user, 15)


if __name__ == "__main__":
    main()
