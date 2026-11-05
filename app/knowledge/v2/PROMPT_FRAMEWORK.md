# Prompt Framework

This document defines how the knowledge base assembles into the actual request sent to the AI provider. It is the one place that explains the *mechanics* of assembly — every other document in this folder defines *content* (identity, principles, sound methodology, rules, voice, format, examples).

## Two categories of document

Not every file in this folder is transmitted to the AI on every request. That would be wasteful (these documents overlap on purpose, for a human reader's sake) and, for two of them, would contradict what they say about themselves.

### Assembled into every generation request, in this order

1. `CONSTITUTION.md` — identity and immutable principles
2. `STYLE_GUIDE.md` — voice and tone
3. `PHONETIC_ENGINE.md` — the Uzbek sound-association methodology (V2 addition — previously folded into `PROMPT_RULES.md` as a single step; broken out because it's the single highest-leverage piece of the system and deserved its own systematic treatment)
4. `PROMPT_RULES.md` — the concrete, numbered generation rules
5. `RESPONSE_SPECIFICATION.md` — the exact output contract
6. `EXAMPLES.md` — good/bad few-shot demonstrations
7. *(request-time only)* `regenerate_avoid.md` — inserted only when the learner tapped "Generate Another Mnemonic"
8. *(request-time only)* `user_prompt.md` — inserts the actual word being asked about; always last

### Reference-only — inform the documents above, not retransmitted

- `PHILOSOPHY.md` and `MEMORY_SCIENCE.md` describe the reasoning behind the system, not instructions for it. Their substance is already distilled into prompt-appropriate form inside `CONSTITUTION.md` and `PHONETIC_ENGINE.md`. Sending the full essays on every API call would repeat that reasoning at real token cost without changing model behavior.
- `EVALUATION_GUIDE.md` and `TEST_CASES.md` are for humans (and a future automated QA harness) reviewing mnemonic quality *after* generation — they don't belong in a request asking the model to *generate* something.

If you disagree with this split for a specific document, moving it into the assembled list is a one-line change in `manifest.yaml` — no Python changes required.

## How assembly actually happens

`manifest.yaml` in this same folder declares the `prompt_components` list above, in order. `PromptBuilder` (in `app/services/ai/knowledge_engine/builder.py`) loads each one, validates the whole set, substitutes `$word` / `$avoid_items` placeholders via `string.Template` (not `str.format()` — `RESPONSE_SPECIFICATION.md` contains literal JSON with `{`/`}` characters that `.format()` would misinterpret as placeholders), and concatenates everything into one final string. That string — and nothing else — is what the active `AIProvider` ever sees.

## Adding a new document

- **New file assembled into every request:** add the `.md` file here, add its name to `manifest.yaml`'s `prompt_components` list at the position you want it concatenated.
- **New reference-only file:** add the `.md` file here, add its name to `manifest.yaml`'s `reference_only` list (purely for tracking — nothing reads this list programmatically).
- **A new version of the whole knowledge base (v3):** copy this folder to `app/knowledge/v3/`, update `version:` in its `manifest.yaml` to `v3` (the validator will reject a mismatch), then point `MNEMONIC_PROMPT_VERSION=v3` (or `settings.mnemonic_prompt_version`) at it.
