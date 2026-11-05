# Prompt Framework

This document defines how the knowledge base assembles into the actual request sent to the AI provider. It is the one place that explains the mechanics of assembly; every other document defines content.

## Two categories of document

### Assembled into every generation request, in this order
1. `CONSTITUTION.md` — purpose, principles, priority order
2. `STYLE_GUIDE.md` — Uzbek language standards and voice (STRICT and PREFERENCE rules)
3. `PROMPT_RULES.md` — the seven-step generation process and input-handling rules
4. `RESPONSE_SPECIFICATION.md` — the formal success/error contract
5. `EXAMPLES.md` — positive, error, regeneration and negative demonstrations
6. *(request-time only)* `regenerate_avoid.md` — inserted only when the learner tapped "Generate Another Mnemonic"
7. *(request-time only)* `user_prompt.md` — inserts the entry being asked about; always last

### Reference-only — not retransmitted
`PHILOSOPHY.md`, `MEMORY_SCIENCE.md`, `EVALUATION_GUIDE.md` and `TEST_CASES.md` explain or test the system. They do not belong in a request asking the model to generate something. Moving one into `prompt_components` is a one-line change in `manifest.yaml`.

## How assembly happens
`manifest.yaml` declares `prompt_components` in order. The builder loads each file, concatenates them, and substitutes `$word` and `$avoid_items` with `string.Template` (not `str.format()`, because the Response Specification contains literal `{` and `}`).

Rules that keep this safe:
- Assembled documents must contain no dollar sign other than the two placeholders (checked by `tests/`).
- `string.Template` substitutes in one pass and never re-scans substituted values, so a value containing `$word` or `${...}` stays literal. Do not substitute twice on the same string, and do not insert one template's result into another before substituting.
- The entry is untrusted. Validate and normalize it in code before substitution (`integration/input_guard.py`). The prompt also tells the model to treat it as data, but that is a second line of defense, not the first.

## System message and user message
When the provider API supports a separate system instruction, send the static components as the system instruction, and the optional regeneration block plus the user prompt as the user message. `integration/prompt_assembly.py` returns exactly that split. When the provider has no such split, concatenate system text, then user text, in that order.

## Enforcement in code
The prompts ask for a response contract; the application enforces it. `integration/response_contract.py` normalizes, validates and classifies responses, and `integration/generation.py` wraps a provider call with retries and logging. See `README.md` at the package root.

## Adding a new document
- Assembled into every request: add the `.md` file here and its name to `prompt_components` at the position you want. Re-run the tests.
- Reference-only: add the file and list it under `reference_only`.
- A new version of the whole knowledge base: copy this folder to a new version folder and follow the Version Manager section of the main README.
