# Knowledge Engine

How MemoraBot's mnemonic prompt is built, why it's structured this way, and
how to extend it — for new content, new versions, new prompt sets, and new
AI providers.

## The problem this solves

Before V1.2, the entire mnemonic prompt was one large Python string
(`prompts.py`). Editing it meant editing code. Versioning it meant editing
code and remembering what the last version looked like. Every future AI
provider would have needed its own copy of that string, or a fragile shared
import. `app/knowledge/` and the engine described here replace all of that
with plain Markdown files a non-programmer can edit, plus a small,
completely generic Python layer that assembles them.

## Layers

```
app/services/ai/
├── knowledge_engine/              GENERIC — knows nothing about "mnemonic"
│   ├── version_manager.py            resolves/lists versions on disk
│   ├── loader.py                     reads manifest.yaml + .md files (async)
│   ├── validator.py                  checks missing/empty/duplicate/version issues
│   ├── builder.py                    orchestrates the above, returns one final string
│   └── exceptions.py                 KnowledgeEngineError + 4 subclasses
│
├── mnemonic_prompt.py              THIN ADAPTER — the only file that knows
│                                     the knowledge base lives at
│                                     app/knowledge/<version>/, or that
│                                     regeneration needs an extra template
│
└── prompts/  (doesn't exist — content lives in app/knowledge/, one level up
               from app/services/, since it's project-wide knowledge, not
               AI-package-internal data)
```

`GeminiProvider` calls exactly one function —
`mnemonic_prompt.build_mnemonic_prompt(word, avoid, version)` — and gets a
plain string back. It has zero knowledge of Markdown files, YAML, or
directory layouts. That's deliberate: "GeminiProvider must never know how
prompts are built."

## `app/knowledge/v1/` — what's in it and why

| File | Sent to the AI? | Purpose |
|---|---|---|
| `manifest.yaml` | No (config) | Declares assembly order + version tag |
| `CONSTITUTION.md` | Yes | Identity + immutable principles |
| `STYLE_GUIDE.md` | Yes | Voice and tone |
| `PROMPT_RULES.md` | Yes | The numbered generation rules |
| `RESPONSE_SPECIFICATION.md` | Yes | The exact JSON output contract |
| `EXAMPLES.md` | Yes | Good/bad few-shot demonstrations |
| `user_prompt.md` | Yes, always last | Template: inserts `$word` |
| `regenerate_avoid.md` | Yes, only on regenerate | Template: `$avoid_items` |
| `PHILOSOPHY.md` | No | Reference — the long-term vision |
| `MEMORY_SCIENCE.md` | No | Reference — the research basis |
| `EVALUATION_GUIDE.md` | No | Empty — reserved for a future human/automated QA rubric |
| `TEST_CASES.md` | No | Empty — reserved for future regression test scenarios |

### Why PHILOSOPHY.md and MEMORY_SCIENCE.md aren't sent to the AI

Both documents explicitly describe themselves as background, not
instructions — MEMORY_SCIENCE.md says outright: *"It is not a prompt... it
is the scientific foundation."* Their substance is already distilled into
prompt-appropriate form inside CONSTITUTION.md (e.g. its Article 6: "Facts
are forgotten. Stories are remembered."). Retransmitting the full essays on
every single generation call would repeat that same reasoning at real,
recurring token cost without giving the model anything new to act on. This
reasoning is also written into `app/knowledge/v1/PROMPT_FRAMEWORK.md`
itself, so it's discoverable from inside the knowledge base, not just here.

If you disagree for a specific document, moving it into
`manifest.yaml`'s `prompt_components` list is a one-line change — no Python
edits needed.

## `manifest.yaml`

```yaml
version: v1
description: "..."
prompt_components:      # loaded, validated, and concatenated in THIS order
  - CONSTITUTION.md
  - STYLE_GUIDE.md
  - PROMPT_RULES.md
  - RESPONSE_SPECIFICATION.md
  - EXAMPLES.md
reference_only:         # tracked for documentation only; never loaded
  - PHILOSOPHY.md
  - MEMORY_SCIENCE.md
  - EVALUATION_GUIDE.md
  - TEST_CASES.md
```

`user_prompt.md` and `regenerate_avoid.md` are deliberately **not** in
`prompt_components` — they're request-specific templates that
`mnemonic_prompt.py` loads separately via the builder's `extra=` parameter,
appended after the static components.

## Validation

`KnowledgeValidator` checks, every time a prompt is built:

- **Invalid configuration** — `prompt_components` is empty, or lists the
  same filename twice.
- **Invalid version** — `manifest.yaml`'s own `version:` field doesn't match
  the version folder it's found in (catches a copied `v1/ → v2/` folder
  where you forgot to update the field inside it).
- **Missing files** — any file `prompt_components` (or `extra`) references
  doesn't exist on disk.
- **Empty files** — any referenced file is blank/whitespace-only.
- **Duplicate sections** — the same Markdown header (e.g. `## Purpose`)
  appears twice *within a single file*.

That last check is scoped to within-file on purpose. An early version of
this validator checked *across* files and immediately flagged a false
positive: both `STYLE_GUIDE.md` and `PROMPT_RULES.md` legitimately open
with `## Purpose`, a normal documentation convention, not a mistake. The
check was narrowed to catch what it's actually meant to catch — an
accidental double-paste within one document — without punishing consistent
structure across several.

`factory.create_ai_provider()` runs this validation once, eagerly, at
startup, before ever handing back a real `GeminiProvider` — a broken
knowledge file is caught immediately with a clear log message and a
fallback to `MockProvider`, the same pattern already used for a missing
`GEMINI_API_KEY`.

## Templating: `$word`, not `{word}`

Placeholders use Python's `string.Template` (`$word`, `$avoid_items`), not
`str.format()` (`{word}`). `RESPONSE_SPECIFICATION.md` contains literal
JSON examples full of `{` and `}` characters — `.format()` would try to
parse those as placeholders and crash. `$`-style substitution doesn't
collide with that at all, so every component can be processed the same
uniform way regardless of whether it happens to contain JSON.
`.safe_substitute()` is used specifically so a stray `$` in prose (which
none of the current files have, but might in the future) doesn't crash the
whole pipeline — unmatched placeholders are left as literal text.

## Prompt version

`GeminiProvider(prompt_version=...)` is injected from
`settings.mnemonic_prompt_version` (env var `MNEMONIC_PROMPT_VERSION`,
default `v1`) exactly the way `model` already was. Every generated
`mnemonic_history` row records which `prompt_version` produced it, enabling
future "which prompt version performs better" analytics
(`AnalyticsRepository.prompt_version_performance`, already built — see
`docs/MNEMONIC_LIBRARY.md`).

### Adding a new file to the current version

1. Add the `.md` file under `app/knowledge/v1/`.
2. Add its filename to `manifest.yaml`'s `prompt_components` (or
   `reference_only`, if it shouldn't be sent to the AI).

No Python changes. `KnowledgeLoader`/`PromptBuilder` discover it purely
from that list.

### Adding a new version (v2)

1. Copy `app/knowledge/v1/` to `app/knowledge/v2/`.
2. Edit the Markdown however you want.
3. **Update `version: v2`** inside the copied `manifest.yaml` — the
   validator rejects a mismatch here on purpose.
4. Set `MNEMONIC_PROMPT_VERSION=v2` in `.env`.

That env var is the only code-adjacent change required; everything else is
content. `KnowledgeVersionManager.list_versions()` is already written and
ready for a future Admin Panel "Prompt Version Information" screen to
enumerate available versions without any new machinery.

## Adding a new AI provider (e.g. OpenAI, Claude, a local GGUF model)

1. Create `app/services/ai/openai_provider.py` implementing `AIProvider`:
   `name`, `prompt_version` properties + `async generate_mnemonic(word, avoid)`.
2. Inside it, call the exact same
   `mnemonic_prompt.build_mnemonic_prompt(word, avoid, version)` that
   `GeminiProvider` calls — it already returns a plain, provider-agnostic
   string; there's nothing Gemini-specific about it.
3. Add one branch to `app/services/ai/factory.py::create_ai_provider()`.

`MnemonicService`, every handler, and the Knowledge Engine itself never
change. This is the concrete payoff of the whole architecture: a new
provider is a new HTTP/SDK call and response parser, nothing else.

## Adding a whole new prompt-consuming feature (e.g. a future AI Chat)

1. Create `app/knowledge/chat/v1/` (note: a new top-level knowledge base,
   sibling to the mnemonic one) with its own `manifest.yaml` and `.md` files.
2. Create `app/services/ai/chat_prompt.py`, shaped exactly like
   `mnemonic_prompt.py`, pointing its `KnowledgeVersionManager` at
   `app/knowledge/chat/` instead.
3. `knowledge_engine/` needs zero changes — it was never aware "mnemonic"
   existed as a specific concept in the first place; it only ever operated
   on whatever `Path` and `version` string it was given.
