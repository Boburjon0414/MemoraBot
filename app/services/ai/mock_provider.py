"""Offline `AIProvider` implementation used for local development and demos.

Demonstrates that the AIProvider abstraction genuinely supports swapping
implementations: MemoraBot runs and the whole MneVoca flow is testable even
before a real GEMINI_API_KEY is configured (see `app.services.ai.factory`).
"""

from __future__ import annotations

import asyncio
import random

from app.core.enums import DifficultyLevel
from app.services.ai.base import AIProvider
from app.services.ai.schemas import MnemonicResult


class MockProvider(AIProvider):
    """Produces a clearly-labeled, deterministic-shape mnemonic without any network access."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def prompt_version(self) -> str:
        return "mock"

    async def generate_mnemonic(self, word: str, avoid: list[str] | None = None) -> MnemonicResult:
        await asyncio.sleep(0)  # keep this genuinely async, for realistic testing
        difficulty = random.choice(list(DifficultyLevel))
        variant = random.randint(100, 999)
        version_note = f", {len(avoid)} avoided" if avoid else ""
        return MnemonicResult(
            word=word,
            meaning=f"'{word}' so'zining ma'nosi (demo rejim{version_note})",
            uzbek_pronunciation=f"'{word}' so'zi taxminan '{word}-{variant}' deb talaffuz qilinadi (demo)",
            mnemonic_story=(
                f"Demo rejimida ishlayapsiz (variant #{variant}): '{word}' so'zi uchun hozircha "
                "haqiqiy AI xotira hikoyasi mavjud emas. Buni yoqish uchun .env faylida "
                "GEMINI_API_KEY ni sozlang."
            ),
            example_sentence=f"This is an example sentence with the word '{word}'.",
            difficulty=difficulty,
        )
