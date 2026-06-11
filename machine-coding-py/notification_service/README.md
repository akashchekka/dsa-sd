# Notification Service

Topic-based pub-sub notifier with multi-channel delivery (Email / SMS / Push), parallel fan-out, and retry-with-backoff on failures.

## Run

```pwsh
cd machine-coding-py
python -m notification_service
```

## The subject

**Problem.** An application needs to tell users things — order confirmations, price drops, security alerts, marketing campaigns. Each user might prefer email, SMS, push, or all three. The system accepts a message + topic from the publisher, finds every subscriber to that topic, and delivers via each subscriber's chosen channel — handling failures, retries, and slow downstream providers gracefully.

**Why it's a classic interview problem.** Looks like "send some emails" but actually exercises distributed-systems thinking at a small scale:

- **Decoupling publisher from delivery mechanics.** The code that says "the price dropped" should not know about SMTP, Twilio, FCM, or retries. It calls `notify("deals", msg)` and moves on. Channels and retries live behind interfaces.
- **Multi-channel as Strategy pattern.** Email, SMS, and Push share nothing operationally (different APIs, latencies, failure modes) but have one common contract: `send(destination, payload)`. The interface is what makes adding Slack a 30-line change.
- **Fan-out + parallelism.** One publish reaches N subscribers. Sending them serially makes a campaign O(N) latency. Parallel fan-out (async / threads) makes it O(slowest). Recognizing this — and choosing `asyncio.gather` vs. a thread pool vs. a job queue — is the design choice.
- **Retries with backoff.** Transient failures (network blip, throttling) should retry; permanent failures (invalid number) should not. Exponential backoff (`2^n`) prevents thundering-herd retries from making things worse. This is the classic "retry-policy as separated concern" pattern.
- **Failure isolation.** If SMS provider is down, email and push must still go out. One bad subscriber must not poison the whole publish.
- **The escalations are real.** *Templating per subscriber. Quiet hours. Rate limits per channel. Dead-letter queue. Read receipts. GDPR-compliant opt-out.* — each is a real product requirement, and the design must accommodate them without rewriting.

**Where this lives.** Every consumer-facing product: e-commerce order updates, SaaS alerts, banking 2FA codes, social-app friend requests, marketing platforms (Mailchimp, OneSignal, SendGrid).

**Core mental model.**
```
publish(topic, payload)
   → subs = subscriptions[topic]
   → for each sub in parallel:
        retry_policy.execute(
           channel[sub.channel].send(sub.destination, payload)
        )
```

**Core concepts exercised.** Strategy pattern (channels, retry policies), async I/O (`asyncio.gather`), Observer pattern (pub-sub), Decorator pattern (retry wraps channel), failure isolation, separation of transport ("how to send") from policy ("when to retry").

## What's implemented

`NotificationService` keeps `(topic → list[Subscription])`. `publish(topic, msg)` is async — it fans out to all matching subscribers in parallel via `asyncio.gather`, each delivery going through its channel-specific strategy (`EmailChannel`, `SmsChannel`, `PushChannel`) wrapped in an `IRetryPolicy` (exponential backoff).

## File layout

```
notification_service/
├── __main__.py                       # demo: 3 subscribers on "deals", different channels
├── models/
│   ├── notification.py               # Notification (id, payload, attempt count)
│   └── subscription.py               # Subscription + Channel enum
├── interfaces/
│   ├── notification_channel.py       # INotificationChannel.send(destination, payload)
│   └── retry_policy.py               # IRetryPolicy.execute(coro_factory)
├── strategies/
│   ├── channels.py                   # EmailChannel, SmsChannel, PushChannel
│   └── exponential_backoff_retry.py  # 2^n delay, capped attempts
└── services/
    └── notification_service.py       # subscribe / publish (async)
```

## Key design choices

| Concern | Decision | Why |
|---|---|---|
| **Multi-channel delivery** | `INotificationChannel` (Strategy pattern) | Add Slack, Webhook, In-App as new strategies; no service changes |
| **Async fan-out** | `await asyncio.gather(*sends)` | A slow SMS provider doesn't block the email blast |
| **Retry policy as separate concern** | `IRetryPolicy.execute(callable)` | Decorator-style; channel logic doesn't know about retries |
| **Exponential backoff** | `2^attempt` seconds, capped attempts | Standard pattern; avoids thundering-herd retry |
| **Subscription as value object** | `@dataclass(frozen=True)` — user, topic, channel, destination | One user can subscribe to same topic on multiple channels (Email + Push) |
| **Failure isolation** | Per-subscriber try/except inside gather | One subscriber's failure doesn't poison the publish |

## Why `asyncio` here?

Channel sends are **I/O-bound** (HTTP to SMTP, Twilio, FCM, etc.). Threads work but are heavier; async lets one event loop fan out to hundreds of subscribers cheaply. Each `send()` is a coroutine — `gather` schedules them all concurrently.

## How to extend

| Add… | Change |
|---|---|
| **New channel** (Slack, WebPush) | Implement `INotificationChannel`; register in service constructor |
| **Different retry strategies** | `LinearBackoff`, `JitteredBackoff` implementing `IRetryPolicy` |
| **Dead-letter queue** | Catch exhausted retries in service, persist to DLQ |
| **Templating** | `ITemplateEngine` for personalized payloads per subscriber |
| **Topic wildcards** | Replace exact-match dict with a trie / matcher (see `pub_sub/` for example) |
| **User preferences** (do-not-disturb, quiet hours) | Filter subscriptions before fan-out |
| **Rate limiting per channel** | Wrap each channel with the limiter from `rate_limiter/` |

## Edge cases handled

- A failing channel doesn't block others — each is awaited independently inside `gather`.
- Retry exhaustion logged; doesn't crash the publish.
- Subscribing the same user twice to the same topic+channel — the design allows it (semantically idempotent for end-user; dedupe is a policy choice).

## Out of scope

- Persistent message store / replay.
- Cross-process delivery (this is in-memory; real systems use Kafka/SQS).
- Auth and subscription consent flows.
- Read receipts / delivery confirmation back to publisher.

## Contrast with `pub_sub/`

`pub_sub/` is a general-purpose in-memory message broker with worker threads, backpressure, and wildcard topics. `notification_service/` is the **application layer** — it knows about users, channels (Email/SMS/Push), and retries. Both could compose: notification service publishes to a pub-sub broker for inter-service delivery.
