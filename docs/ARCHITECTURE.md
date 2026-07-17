# Architecture — V1.2

This document is the entry point for understanding what V1.2 changed and
why. It assumes familiarity with the original MemoraBot layering
(handlers → services → repositories → database); see the main `README.md`
for that baseline. This file covers only what's new.

## What V1.2 is, in one paragraph

The mnemonic prompt moved out of Python entirely and into a versioned,
Markdown-authored knowledge base (`app/knowledge/`), assembled at request
time by a new generic **Knowledge Engine**. On top of that, `mnemonic_history`
became a genuine **self-improving library**: every version accumulates
usage and rating statistics, the system serves the highest-rated *active*
version of a word instead of just the most recent one, and consistently
poor versions are automatically retired (never deleted). A **free-plan
quota** was added on top, and a read-only **analytics data layer** now
exists for a future admin dashboard to consume. No handlers, no database
tables (only new columns on two existing tables), and no existing business
logic call sites broke — the whole thing was inspected file-by-file and
verified where genuinely testable (see "What was actually tested" below).

## Folder structure (new/changed parts only)

```
memorabot/
├── docs/                                    <- NEW: this documentation set
│   ├── ARCHITECTURE.md                        (this file)
│   ├── KNOWLEDGE_ENGINE.md                    prompt engine + how to extend it
│   ├── MNEMONIC_LIBRARY.md                    caching/rating/self-improvement + DB schema
│   └── ROADMAP.md                              analytics, admin panel, premium, referral proposals
├── alembic/versions/
│   └── 0003_mnemonic_stats_and_cefr.py       <- NEW migration
└── app/
    ├── core/
    │   └── enums.py                          <- MODIFIED: DifficultyLevel -> CEFR (A1-C2)
    ├── config.py                             <- MODIFIED: +mnemonic_prompt_version, +free_plan_generation_limit
    ├── bot.py                                <- MODIFIED: await create_ai_provider; pass quota limit
    ├── knowledge/                             <- RESTRUCTURED (your files, relocated + 2 populated)
    │   └── v1/
    │       ├── manifest.yaml                      NEW: assembly order + version tag
    │       ├── CONSTITUTION.md                    (yours, byte-for-byte unchanged, relocated)
    │       ├── STYLE_GUIDE.md                     (yours, unchanged, relocated)
    │       ├── PROMPT_RULES.md                    (yours, unchanged, relocated)
    │       ├── RESPONSE_SPECIFICATION.md          (yours, unchanged, relocated)
    │       ├── PHILOSOPHY.md                      (yours, unchanged, relocated — reference-only)
    │       ├── MEMORY_SCIENCE.md                  (yours, unchanged, relocated — reference-only)
    │       ├── EXAMPLES.md                        NEW CONTENT (was empty)
    │       ├── PROMPT_FRAMEWORK.md                NEW CONTENT (was empty)
    │       ├── EVALUATION_GUIDE.md                still empty (see ROADMAP.md)
    │       ├── TEST_CASES.md                      still empty (see ROADMAP.md)
    │       ├── user_prompt.md                     NEW template ($word)
    │       └── regenerate_avoid.md                NEW template ($avoid_items)
    ├── database/models/
    │   ├── mnemonic_history.py               <- MODIFIED: +9 statistics columns
    │   └── user_settings.py                  <- MODIFIED: +ai_generations_used
    ├── repositories/
    │   ├── mnemonic_repository.py            <- MODIFIED: rating-based serving + lifecycle methods
    │   ├── user_settings_repository.py       <- MODIFIED: +increment_generation_count
    │   └── analytics_repository.py           <- NEW: read-only aggregate queries
    ├── services/
    │   ├── mnemonic_service.py               <- MODIFIED: rating-based get_or_generate, timed generation, regenerate tracking
    │   ├── mnemonic_feedback_service.py       <- MODIFIED: syncs denormalized stats, auto-deactivation
    │   ├── usage_service.py                  <- NEW: free-plan quota
    │   ├── analytics_service.py              <- NEW: thin wrapper over AnalyticsRepository
    │   └── ai/
    │       ├── base.py                       <- MODIFIED: +prompt_version abstract property
    │       ├── schemas.py                    <- MODIFIED: default difficulty B1 (was MEDIUM)
    │       ├── gemini_provider.py            <- MODIFIED: knowledge engine integration, CEFR schema
    │       ├── mock_provider.py              <- MODIFIED: +prompt_version property
    │       ├── factory.py                    <- MODIFIED: async, validates knowledge base at startup
    │       ├── mnemonic_prompt.py            <- NEW: thin mnemonic-specific adapter (replaces prompts.py)
    │       ├── prompts.py                    <- DELETED (fully superseded)
    │       └── knowledge_engine/             <- NEW PACKAGE (generic, feature-agnostic)
    │           ├── version_manager.py
    │           ├── loader.py
    │           ├── validator.py
    │           ├── builder.py
    │           └── exceptions.py
    ├── middlewares/services.py               <- MODIFIED: injects UsageService; constructor takes quota limit
    ├── handlers/mnevoca.py                    <- MODIFIED: quota check; regenerate passes source id
    ├── utils/formatters.py                   <- MODIFIED: CEFR difficulty display
    ├── texts/messages.py                     <- MODIFIED: CEFR labels + free-plan limit message
    ├── requirements.txt                      <- MODIFIED: +PyYAML
    └── .env.example                          <- MODIFIED: documents new settings
```

**Untouched:** every handler except `mnevoca.py`, the entire database layer
except the two column additions above, `MnemonicHistory`/`User` model
relationships, all keyboards except none (callback shapes were already
correct from V1.1), FSM states, and all business logic in
`user_service.py` / `settings_service.py`.

## What was actually tested

This sandbox has no network access, so aiogram/SQLAlchemy/pydantic
couldn't be installed and the bot couldn't be run against real Telegram or
Gemini servers. Three things *were* genuinely exercised, not just
syntax-checked:

1. **The Knowledge Engine**, end-to-end, against your real relocated
   knowledge files — including a real bug it caught (see
   `docs/KNOWLEDGE_ENGINE.md`) that was then fixed and re-verified.
2. **Migration 0003's actual SQL**, run against a copy of your real
   `memorabot.db` — verified all 6 existing rows survived, difficulty
   values were correctly reclassified, and your 2 real ratings correctly
   backfilled into the new `likes`/`average_rating` columns (see
   `docs/MNEMONIC_LIBRARY.md` for the before/after).
3. **The rating-based serving and auto-deactivation logic** in
   `MnemonicService`/`MnemonicFeedbackService`, using hand-written fake
   repositories that implement the same interface as the real ones —
   7 scenarios covering cache hit/miss, vote-flipping, and both
   deactivation triggers, all passing.

Everything else (aiogram wiring, the actual Gemini HTTP call, handler
plumbing) was written carefully against the same patterns already proven
to work in your live bot, cross-checked with an import-consistency script
(143 `from app...` imports, all resolving correctly), but not executed. A
real `python run.py` test is worth doing before relying on this.

## SOLID / Clean Architecture mapping

- **SRP** — `KnowledgeLoader` reads, `KnowledgeValidator` checks,
  `PromptBuilder` assembles: three separate reasons to change. Likewise
  `MnemonicRepository` (data access) vs `MnemonicService` (business rules:
  which version to serve, when to deactivate) vs `AnalyticsRepository`
  (cross-cutting reporting, deliberately not mixed into `MnemonicRepository`).
- **OCP** — new knowledge files, new knowledge-base versions, and new
  prompt sets (chat, statistics, ...) are pure additions; nothing existing
  is edited. Same for AI providers: implement `AIProvider`, add one factory
  branch.
- **LSP** — `GeminiProvider` and `MockProvider` are fully interchangeable
  behind `AIProvider`, now including the `prompt_version` property.
- **ISP** — `AnalyticsRepository` doesn't extend the entity-CRUD
  `BaseRepository` — it's a different shape (cross-cutting queries), so it
  isn't forced to implement `get_by_id`/`add`/etc. it has no use for.
- **DIP** — `MnemonicService` depends on `AIProvider` (abstract) and
  `MnemonicRepository` (abstract data access), never on `GeminiProvider` or
  raw SQL. `PromptBuilder` depends on the loader/validator abstractions
  it's constructed with, not concrete file-reading code inline.

## How to maintain this project going forward

- **Changing mnemonic generation behavior:** edit a `.md` file in
  `app/knowledge/v1/`. No Python change, no deployment of new code — just
  the content. See `docs/KNOWLEDGE_ENGINE.md`.
- **Adjusting the self-improving thresholds** (currently: 3 dislikes or 3
  regenerations deactivates a version): these are named constants at the
  top of `mnemonic_service.py` and `mnemonic_feedback_service.py`
  (`_REGENERATION_DEACTIVATION_THRESHOLD`, `_DISLIKE_DEACTIVATION_THRESHOLD`)
  — starting heuristics, not tuned values; adjust as real usage data comes in.
- **Schema changes:** always via a new Alembic migration (see `0003` as the
  template for adding columns + backfilling data safely). Never edit an old
  migration once it may have run against a real database.
- **Before any future large change:** read `docs/ROADMAP.md` first — it
  documents what's deliberately deferred and why, so a future session
  doesn't accidentally duplicate effort or make a premature commitment
  (payment provider, admin auth model, etc.) that should be a product
  decision, not an implementation default.
