"""
=============================================================================
 LoggingFramework — entry point
=============================================================================
 Run:  python -m logging_framework   (from machine-coding-py/)

 Note: we don't use the stdlib `logging` module — the point of the round
 is to design one.
=============================================================================
"""
from __future__ import annotations

from models.log_level                import LogLevel
from services.logger_factory         import LoggerFactory
from strategies.async_appender       import AsyncAppender
from strategies.console_appender     import ConsoleAppender
from strategies.plain_text_formatter import PlainTextFormatter


def main() -> None:
    with AsyncAppender(ConsoleAppender(PlainTextFormatter())) as async_sink:
        factory = LoggerFactory(default_level=LogLevel.DEBUG).add_appender(async_sink)

        auth = factory.get_logger("Auth")
        pay  = factory.get_logger("Payments")

        auth.info("User u1 signed in")
        auth.debug("Token refresh queued")
        pay.warn("Retrying gateway: timeout")
        try:
            raise RuntimeError("card declined")
        except RuntimeError as ex:
            pay.error("Charge failed", ex)
        # context-manager close() drains and joins the worker


if __name__ == "__main__":
    main()
