"""Structured output contract for mnemonic generation.

Every `AIProvider` implementation must return a `MnemonicResult`, regardless
of which underlying model or API it talks to. This is what lets
`MnemonicService` stay completely provider-agnostic.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.core.enums import DifficultyLevel


class MnemonicResult(BaseModel):
    """Structured mnemonic data for a single English word."""

    word: str = Field(..., description="The original English word or short phrase.")
    meaning: str = Field(..., description="Concise meaning/translation of the word.")
    uzbek_pronunciation: str = Field(
        ..., description="An Uzbek-sound approximation of the English pronunciation."
    )
    mnemonic_story: str = Field(
        ..., description="A short, vivid, funny story linking the sound-alike to the meaning."
    )
    example_sentence: str = Field(..., description="An example sentence using the word in English.")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.B1)

    @field_validator("word")
    @classmethod
    def _normalize_word(cls, value: str) -> str:
        return value.strip().lower()
