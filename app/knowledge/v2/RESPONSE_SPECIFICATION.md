# Response Specification

The exact response contract between the AI provider and MemoraBot. Every provider (Gemini, Claude, OpenAI, local models, or future ones) must conform to this. The format must stay stable even if the underlying model changes.

Every response must be complete, predictable, machine-readable, human-friendly, and easy to validate. No required field is ever omitted.

## Required Fields

`word`, `meaning`, `uzbek_pronunciation`, `mnemonic_story`, `example_sentence`, `difficulty` — all mandatory.

- **word** — the original English word, exactly as given, preserving spelling, no symbols or explanations. Example: `acquire`.
- **meaning** — the primary Uzbek meaning, short and natural. Good: `egallamoq`. Bad (too long, dictionary-style): `Biror narsani qo'lga kiritish yoki egalik qilish ma'nosini bildiruvchi fe'l.`
- **uzbek_pronunciation** — the memory bridge, not a pronunciation guide. Format as `"<anchor>" — <short reason it echoes the English sound>`, e.g. `"KICH-en" — "kichik" so'ziga o'xshab eshitiladi`. Natural, easy to say, short.
- **mnemonic_story** — 20–60 words, contains action and emotion, easy to visualize, follows Prompt Rules and the Constitution.
- **example_sentence** — one natural, CEFR-appropriate English sentence using the word.
- **difficulty** — exactly one of `A1`, `A2`, `B1`, `B2`, `C1`, `C2`. No other values.

## Forbidden Content

Grammar explanations, IPA transcription, long dictionary definitions, AI reasoning or internal thinking, any Markdown syntax (tables, `**bold**`, `_italic_`, backticks) — the app renders these fields as raw HTML text, so Markdown characters would appear as literal asterisks/underscores to the user — multiple stories, multiple meanings unless explicitly requested.

## Validation Rules

Invalid if: any required field is missing or empty; the story exceeds the length target; `difficulty` isn't one of the six CEFR values.

## Error Handling

If the AI cannot confidently generate a mnemonic, it must never invent meaningless output — it should return a structured error and let the application decide how to handle it.

## Consistency and Future Compatibility

All providers follow exactly this structure so that switching providers never requires changing Telegram handlers. New fields may be added in future versions; existing fields stay backward compatible whenever possible. The AI returns structured information; MemoraBot decides how it's displayed. These responsibilities stay separate.
