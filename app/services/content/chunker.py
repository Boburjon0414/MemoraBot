"""TextChunker: splits a document's extracted text into overlapping windows.

Algorithm
---------
We want chunks that are:
  1. Small enough to fit alongside several others in an AI context window.
  2. Large enough to contain complete thoughts (not mid-sentence cuts).
  3. Slightly overlapping so that retrieval never misses a phrase that
     straddles a boundary.

Implementation
--------------
We split on sentence boundaries (`. `, `? `, `! `, `\n\n`) rather than
raw character counts.  We accumulate sentences into a window until the
word count would exceed `chunk_size`.  When a window is full:
  - It is emitted as a chunk.
  - The last `overlap` words are carried over into the next window.

Word count is used as the token approximation (English: ~0.75 tokens/word,
so chunk_size=400 words ≈ 530 tokens — comfortably under the 512-token
sweet spot for most embedding models without ever exceeding it).

Upgrade path
------------
When a real tokenizer is warranted (e.g. tiktoken for OpenAI embedding
models, or the SentencePiece tokenizer for Gemini), the `_word_count`
method is the only thing that changes — the rest of the algorithm is
tokeniser-agnostic.
"""

from __future__ import annotations

import re


class TextChunker:
    """Splits plain text into overlapping chunks suitable for embedding.

    Stateless and safe for concurrent use as a singleton.

    Args:
        chunk_size:  Target maximum word count per chunk.  Chunks may
                     slightly exceed this when a single sentence is longer
                     than the target.  Default: 400 words (~530 tokens).
        overlap:     Number of words to repeat at the start of the next
                     chunk.  Provides continuity across chunk boundaries.
                     Default: 60 words (~80 tokens, ~15% of chunk_size).
        min_chunk_size: Minimum word count for a chunk to be emitted.
                     Prevents tiny trailing chunks from polluting the index.
                     Default: 30 words.
    """

    def __init__(
        self,
        chunk_size: int = 400,
        overlap: int = 60,
        min_chunk_size: int = 30,
    ) -> None:
        if overlap >= chunk_size:
            raise ValueError(
                f"overlap ({overlap}) must be smaller than chunk_size ({chunk_size})"
            )
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._min_chunk_size = min_chunk_size

    def chunk(self, text: str) -> list[str]:
        """Split `text` into overlapping chunks and return them as a list.

        Returns an empty list for empty / whitespace-only input.
        Returns a single-element list when the text is shorter than
        `chunk_size` (the entire text is one chunk).
        """
        text = text.strip()
        if not text:
            return []

        sentences = self._split_sentences(text)
        if not sentences:
            return []

        chunks: list[str] = []
        current_words: list[str] = []

        for sentence in sentences:
            sentence_words = sentence.split()
            if not sentence_words:
                continue

            # If this single sentence exceeds chunk_size, emit it as its own
            # chunk rather than skipping it.
            if len(sentence_words) > self._chunk_size:
                # Flush current buffer first
                if self._word_count(current_words) >= self._min_chunk_size:
                    chunks.append(" ".join(current_words))
                current_words = []
                # Emit the long sentence in sub-chunks
                for sub in self._hard_split(sentence_words):
                    chunks.append(" ".join(sub))
                continue

            # Would adding this sentence overflow the window?
            if (
                current_words
                and self._word_count(current_words) + len(sentence_words) > self._chunk_size
            ):
                # Emit current window
                chunk_text = " ".join(current_words)
                if self._word_count(current_words) >= self._min_chunk_size:
                    chunks.append(chunk_text)

                # Carry over the overlap tail into the next window
                current_words = current_words[-self._overlap:] if self._overlap else []

            current_words.extend(sentence_words)

        # Emit the final window
        if current_words and self._word_count(current_words) >= self._min_chunk_size:
            chunks.append(" ".join(current_words))
        elif current_words and not chunks:
            # Edge case: entire text is shorter than min_chunk_size —
            # emit it anyway so we don't silently drop content.
            chunks.append(" ".join(current_words))

        return chunks

    # ── Private helpers ────────────────────────────────────────────────── #

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences on common terminators and blank lines.

        Uses a simple regex rather than an NLP library to avoid dependencies.
        Good enough for IELTS essays, Wikipedia passages, and PDF extracts —
        the typical MemoraBot content types.
        """
        # Split on sentence-ending punctuation followed by whitespace,
        # or on paragraph breaks (one or more blank lines).
        parts = re.split(r'(?<=[.!?])\s+|\n{2,}', text)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _word_count(words: list[str]) -> int:
        return len(words)

    def _hard_split(self, words: list[str]) -> list[list[str]]:
        """Split an oversized word list into chunk_size-d sub-lists."""
        result = []
        i = 0
        while i < len(words):
            result.append(words[i : i + self._chunk_size])
            i += self._chunk_size - self._overlap
        return result
