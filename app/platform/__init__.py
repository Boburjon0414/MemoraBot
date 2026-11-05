"""Application-lifetime singleton resources.

This package owns objects that are constructed once at startup, shared
across all requests, and shut down cleanly at process exit.

`PlatformContainer` is the only public export.  It is constructed in
`bot.py`'s `main()` and passed to `ServicesMiddleware`, which reads
singletons from it instead of constructing them per-request.

Why this layer exists
---------------------
`ServicesMiddleware.__call__()` runs on every Telegram update.  It is
the right place for per-request objects (repositories, session-scoped
services).  It is the wrong place for heavyweight singletons:

  - An `AIGateway` holds N long-lived `aiohttp.ClientSession` objects —
    one per registered key slot.  Recreating them per-request would
    create and tear down hundreds of TCP connections per minute.
  - Future resources (a vector store client, an embedding model, a
    document processor pool) are similarly expensive to construct and
    have no meaningful per-request state.

Before this step, `bot.py` constructed the `AIGateway` directly and
passed it into `ServicesMiddleware.__init__()`, which stored it as a
private attribute.  `PlatformContainer` formalises that pattern into an
explicit, documented tier so future heavyweight singletons have a clear
home — with a `shutdown()` method that `bot.py`'s `finally` block calls
to close every resource in the right order.
"""

from app.platform.container import PlatformContainer

__all__ = ["PlatformContainer"]
