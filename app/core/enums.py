"""Shared domain enums used across the AI schema, database, and formatting layers."""

from __future__ import annotations

from enum import Enum


class DifficultyLevel(str, Enum):
    """How hard a word is expected to be for a learner, using the CEFR scale
    (A1 easiest -> C2 hardest), per `app/knowledge/v1/RESPONSE_SPECIFICATION.md`.

    Replaces the old easy/medium/hard scale (V1.1) — see the Alembic
    migration that reclassifies existing `mnemonic_history` rows.
    """

    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class Language(str, Enum):
    """UI languages supported by MemoraBot."""

    UZ = "uz"
    EN = "en"
    RU = "ru"
