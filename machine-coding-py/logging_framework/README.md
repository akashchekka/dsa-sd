# Logging Framework

A hand-rolled logging library. **Deliberately does not use Python's `logging` module** — the point of the round is to *design* one.

## Run

```pwsh
cd machine-coding-py
python -m logging_framework
```

## The subject

**Problem.** Every application needs to record what it's doing — for debugging, auditing, monitoring, alerting. A logging framework needs to (a) accept messages from anywhere in the codebase, (b) filter by severity, (c) format them for human or machine consumption, (d) route them to one or more destinations (console, file, network, ELK), and (e) do all of this **without slowing down the application code that calls it**.

**Why it's a classic interview problem.** It's a microcosm of clean architecture — and almost every candidate has *used* a logging library, so it tests whether they understand its design:

- **Three separable concerns** that beginners conflate into one method: **filtering** ("do I care about this level?"), **formatting** ("render this event as a string / JSON / protobuf"), and **appending** ("write the string somewhere"). Each must be its own abstraction or the framework cannot grow.
- **Levels as ordering.** `DEBUG < INFO < WARN < ERROR` — a single integer comparison filters out 99% of events in production. Get this wrong (e.g., string comparison) and filtering breaks.
- **Synchronous vs. asynchronous appending.** A direct file/network write on every `logger.info()` adds latency to every request. The async appender (queue + worker thread) decouples caller latency from sink latency — but introduces its own problems: lost messages on crash, backpressure when sink is slow, clean shutdown without orphan threads.
- **Decorator pattern in its purest form.** `AsyncAppender(ConsoleAppender(JsonFormatter()))` — wrapping changes behavior without changing the wrapped class. Same idea as buffered streams in C++/Java.
- **Logger hierarchy / naming.** `Logger("Payments.Gateway")` should inherit configuration from `"Payments"` if not overridden. The Factory pattern is what makes this work — never call `Logger()` directly.
- **The horrible failure mode** to avoid: an exception inside the logger crashes the request being logged. Logging must be best-effort and silent on its own failures.

**Why building one is illuminating.** Python's `logging` module, log4j, slf4j, Serilog — all follow the same shape: **Logger → Filter → Formatter → Appender**. Building it from scratch shows you understand *why* the production libraries look the way they do.

**Where this matters.** Every production system. Bad logging architecture means either crippled visibility ("why did this fail?") or crippled performance ("why is every request 100ms slower?"). Often both.

**Core mental model.**
```
logger.info("msg")
   → if level >= configured: build LogEvent
   → for each appender:
        formatter.format(event) → string
        sink.write(string)        # may be async via decorator
```

**Core concepts exercised.** Single Responsibility Principle (filter / format / append are 3 things), Decorator pattern (async wraps sync), Factory pattern (logger naming), producer-consumer (async worker), graceful shutdown, fail-silent for non-essential subsystems.

## What's implemented

- **Loggers** named per component (`"Auth"`, `"Payments"`) with configurable level filtering.
- **Appenders** — output sinks (`ConsoleAppender`; trivially `FileAppender`).
- **Formatters** — turn a `LogEvent` into a string (`PlainTextFormatter`; trivially `JsonFormatter`).
- **Async appender** — non-blocking decorator; writes go to a queue, a worker thread drains it.
- **Factory** — `LoggerFactory.get_logger(name)` reuses loggers per name.

## File layout

```
logging_framework/
├── __main__.py                       # demo: Auth + Payments loggers, async console
├── models/
│   ├── log_level.py                  # LogLevel (IntEnum: DEBUG < INFO < WARN < ERROR)
│   └── log_event.py                  # LogEvent (timestamp, level, logger_name, message, exception)
├── interfaces/
│   ├── log_appender.py               # ILogAppender.append(event) + close()
│   └── log_formatter.py              # ILogFormatter.format(event) → str
├── strategies/
│   ├── plain_text_formatter.py       # "[2026-06-03 12:34:56] [INFO] [Auth] User u1 signed in"
│   ├── console_appender.py           # writes to stdout
│   └── async_appender.py             # decorator: queue + worker thread, context-manager friendly
└── services/
    ├── logger.py                     # Logger — debug/info/warn/error, level filtering, fan-out
    └── logger_factory.py             # caches loggers by name, holds appender list + default level
```

## Key design choices

| Concern | Decision | Why |
|---|---|---|
| **Levels as `IntEnum`** | `DEBUG=0 < INFO=1 < WARN=2 < ERROR=3` | Filtering = `if event.level >= logger.level` — single comparison |
| **Appender vs Formatter** | Separate concerns | One appender can use multiple formatters; one formatter shared across appenders |
| **Async appender as decorator** | `AsyncAppender(ConsoleAppender(...))` wraps any sink | Decorator pattern — async is orthogonal to *where* you write |
| **Worker thread + `queue.Queue`** | Producer-consumer | Caller never blocks on disk/network I/O; backpressure via bounded queue (extension point) |
| **Context-manager close** | `with AsyncAppender(...) as sink:` drains and joins | No lost messages on shutdown; no daemon-thread hang |
| **Factory** | One logger per name, lazy-created | Standard logging idiom; cheap to call `get_logger()` repeatedly |
| **Exception attachment** | `error(msg, exception)` captures stack | Useful in real apps; formatter renders the traceback |

## Why async appender?

`logger.info(...)` is called from request-handling hot paths. Synchronous file/network writes add latency to every request. The async appender:

1. Caller enqueues a `LogEvent` — O(1), non-blocking.
2. Worker thread dequeues and writes via the wrapped sync appender.
3. On `close()`, sentinel is enqueued; worker drains then exits cleanly.

## How to extend

| Add… | Change |
|---|---|
| **File appender** | `FileAppender(ILogAppender)` opening a file handle, writes per `append()` |
| **JSON formatter** | `JsonFormatter(ILogFormatter)` returning `json.dumps(event.__dict__)` |
| **Rolling file (size/time)** | `RollingFileAppender` decorating `FileAppender` with rotation logic |
| **Multiple appenders per logger** | Already supported — `factory.add_appender(...)` chains them |
| **Per-logger level override** | `factory.set_level("Payments", LogLevel.DEBUG)` |
| **Structured fields / MDC** | `LogEvent.context: dict[str, Any]`; formatters render it |
| **Drop-on-overflow vs block** | Pass `IBackpressureStrategy` (like `pub_sub/`) to `AsyncAppender` |

## Thread-safety

- `Logger` writes to appenders sequentially (no shared mutable state per call).
- `AsyncAppender` uses `queue.Queue` — thread-safe by design.
- `ConsoleAppender` writes to `sys.stdout` — Python's stdout is line-buffered and thread-safe.

## Edge cases handled

- Logging below configured level — filtered before formatting/appending (no wasted work).
- Process exit with messages in flight — context-manager `close()` drains; explicit `flush()` available.
- Exception inside an appender — caught so it doesn't propagate to the caller and break the request.

## Out of scope

- Distributed log collection (Splunk, ELK shipping).
- Sampling / rate-limiting logs.
- Structured log search.
- Async (`asyncio`) integration — would need an `async def append()` on the interface.
