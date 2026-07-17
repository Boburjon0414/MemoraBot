"""MemoraBot entry point.

Run with:
    python run.py
"""

from __future__ import annotations

import asyncio
import logging

from app.bot import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("MemoraBot stopped by user.")
