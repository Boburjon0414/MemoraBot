# The Self-Improving Mnemonic Library

How caching, rating, regeneration, and automatic quality control work
together, and the exact database schema behind them.

## Database schema (V1.2 additions)

### `mnemonic_history` — 9 new columns (migration 0003)

| Column | Type | Meaning |
|---|---|---|
| `uses` | int, default 0 | Times this version has been served (cache hits + the moment it's generated) |
| `last_used_at` | datetime, nullable | When it was last served |
| `likes` | int, default 0 | Denormalized 👍 count, kept in sync with `mnemonic_feedback` |
| `dislikes` | int, default 0 | Denormalized 👎 count |
| `average_rating` | float, default 0.0 | `(likes - dislikes) / max(1, likes + dislikes)`, range [-1.0, 1.0] |
| `regenerated_count` | int, default 0 | Times a learner tapped "🔄 Generate Another" while viewing THIS version |
| `is_active` | bool, default true, indexed | Soft-delete flag — false means "never serve this again" |
| `response_time_ms` | int, nullable | How long the original Gemini call took |
| `prompt_version` | string, default "v1" | Which `app/knowledge/<version>/` produced this row |

`difficulty` also changed *values* (not type) from `easy`/`medium`/`hard`
to CEFR `A1`–`C2`, per `RESPONSE_SPECIFICATION.md`.

### `user_settings` — 1 new column

| Column | Type | Meaning |
|---|---|---|
| `ai_generations_used` | int, default 0 | Free-plan counter — only incremented on a genuine cache miss |

### Why `average_rating` treats "no feedback" and "50/50 split" the same

Both cases produce `0.0`. This is intentional: both genuinely mean "no
strong signal either way." The tiebreak for equal `average_rating` is
newest-first, which means a brand-new, unrated version is tried ahead of an
old, evenly-split one — a reasonable default exploration bias without
needing a separate "confidence" field.

## Caching mechanism

The cache is **global by word**, not per-user — a good Uzbek mnemonic for
"abandon" doesn't need regenerating separately for every learner, and this
is also a direct cost control (Gemini is only ever called for a word with
no usable existing version).

```
MnemonicService.get_or_generate(user_id, word)
  │
  ├─ MnemonicRepository.get_best_active_by_word(word)
  │     SELECT * FROM mnemonic_history
  │     WHERE word = ? AND is_active = true
  │     ORDER BY average_rating DESC, created_at DESC
  │     LIMIT 1
  │
  ├─ Found? ──────────────────────────────► record_use() → return it
  │                                          (no AI call, ever)
  │
  └─ Not found? (genuinely new word, OR every
     version of this word has been deactivated)
        │
        └─► _generate_and_persist() → calls the AI provider,
            times it, saves a new row (uses=1), returns it
```

A cache "miss" is not only "this word has never been seen" — it also
naturally covers "every previous version of this word turned out to be
bad and got deactivated," which is exactly the self-healing property this
architecture is meant to have: poor content doesn't linger forever, it
gets replaced the next time anyone asks for that word.

## The AI request lifecycle (a genuine cache miss)

```
1. MnemonicService._generate_and_persist(word, avoid=None)
2.   started_at = time.monotonic()
3.   AIProvider.generate_mnemonic(word, avoid)
4.     └─ mnemonic_prompt.build_mnemonic_prompt(word, avoid, version)
5.          └─ PromptBuilder.build(version, extra=[...], word=..., avoid_items=...)
6.               ├─ KnowledgeLoader.load_manifest(version)
7.               ├─ KnowledgeValidator.validate_manifest(...)
8.               ├─ KnowledgeLoader.load_component(...) for each file
9.               ├─ KnowledgeValidator.validate_components(...)
10.              └─ Template(text).safe_substitute(...) for each, joined
11.    └─ aiohttp POST to Gemini generateContent (responseSchema-enforced JSON)
12.    └─ MnemonicResult.model_validate(parsed_json)
13.  response_time_ms = elapsed since step 2
14.  MnemonicRepository.create(..., prompt_version, response_time_ms)
15.  return the new MnemonicHistory row
```

Steps 4–10 are pure, already-tested Knowledge Engine logic (see
`docs/KNOWLEDGE_ENGINE.md`). Steps 11–12 are `GeminiProvider`'s job and
weren't executable in this sandbox (no network) — see `docs/ARCHITECTURE.md`
"What was actually tested" for exactly what was and wasn't verified.

## Regeneration ("🔄 Generate Another Mnemonic")

```
MnemonicService.regenerate(user_id, word, source_mnemonic_id)
  │
  ├─ get_all_by_word(word) → collect every prior version's
  │  uzbek_pronunciation as the "avoid" list for the AI
  │
  ├─ increment_regenerated_count(source_mnemonic_id)
  │  (the SPECIFIC version the learner was looking at)
  │
  ├─ if that version's regenerated_count >= 3:
  │     deactivate(source_mnemonic_id)
  │     (implicit "not good enough" signal, distinct from an explicit 👎)
  │
  └─ _generate_and_persist(word, avoid=[...]) → new row, new "version"
```

Nothing is ever deleted. The newest version simply becomes what future
`get_or_generate` calls prefer — *if* it ends up rated higher than whatever
else is still active.

## Rating mechanism (👍 / 👎)

```
MnemonicFeedbackService.rate(telegram_id, mnemonic_history_id, is_helpful)
  │
  ├─ MnemonicFeedbackRepository.upsert(...)
  │  (unique constraint on (mnemonic_history_id, user_id) — re-tapping
  │   the other button flips the existing row, never adds a duplicate)
  │
  ├─ compute (like_delta, dislike_delta) from (previous_vote, new_vote):
  │     no previous vote            → (+1, 0) or (0, +1)
  │     same vote as before         → (0, 0)   [idempotent re-tap]
  │     flipped vote                → (+1, -1) or (-1, +1)
  │
  ├─ MnemonicRepository.apply_feedback_delta(...)
  │  (adjusts likes/dislikes, recomputes average_rating)
  │
  └─ if dislikes >= 3 AND dislikes > likes:
        deactivate(mnemonic_history_id)
```

Both deactivation triggers (this one, and the regeneration one above) are
named constants — `_DISLIKE_DEACTIVATION_THRESHOLD` in
`mnemonic_feedback_service.py`, `_REGENERATION_DEACTIVATION_THRESHOLD` in
`mnemonic_service.py` — explicitly documented as starting heuristics, not
scientifically tuned values. Adjust them once real usage data suggests a
better threshold.

## Verified against real production data

Before migration 0003 was finalized, its exact SQL was run against a copy
of a real, live `memorabot.db` (1 user, 6 mnemonics, 2 ratings). Results:

| id | word | difficulty before → after | uses | likes | dislikes | average_rating | is_active |
|---|---|---|---|---|---|---|---|
| 1 | travel | easy → **A2** | 1 | 1 | 0 | 1.0 | true |
| 2 | gorgeous | easy → **A2** | 1 | 1 | 0 | 1.0 | true |
| 3 | perform | medium → **B1** | 1 | 0 | 0 | 0.0 | true |
| 4 | consistency | medium → **B1** | 1 | 0 | 0 | 0.0 | true |
| 5 | groggy | medium → **B1** | 1 | 0 | 0 | 0.0 | true |
| 6 | wound | medium → **B1** | 1 | 0 | 0 | 0.0 | true |

All 6 rows preserved (no data loss), difficulty correctly reclassified,
and the 2 real historical ratings (both on rows 1 and 2, both 👍) correctly
backfilled into `likes`/`average_rating` — exactly matching the source
`mnemonic_feedback` data.

## Free-plan quota

```
handlers/mnevoca.py::process_word
  │
  ├─ would_generate = MnemonicService.would_require_generation(word)
  │  (a cheap peek at the cache — same query as get_or_generate's lookup,
  │   just without the side effect of recording a use)
  │
  ├─ if would_generate AND NOT UsageService.has_quota_remaining(telegram_id):
  │     show "free_plan_limit_reached" message, stop
  │     (words already in the library are UNAFFECTED — always free)
  │
  ├─ entry = MnemonicService.get_or_generate(...)
  │
  └─ if would_generate: UsageService.record_generation(telegram_id)
     (only counted AFTER a successful generation, never speculatively)
```

`settings.free_plan_generation_limit` (env var
`FREE_PLAN_GENERATION_LIMIT`, default `3`) is the configurable limit the
task asked for. `UsageService` doesn't yet distinguish free vs. premium
users — see `docs/ROADMAP.md` for why Premium is deliberately deferred, and
exactly where a premium bypass would plug in (`has_quota_remaining`, one
added condition).

## What's proven vs. what's a reasonable design choice awaiting real usage

**Proven correct** (see `docs/ARCHITECTURE.md` for exactly how): the cache
hit/miss logic, the vote-delta computation (including the "flip your vote"
edge case), both deactivation triggers, and the CEFR/stats data migration
against real data.

**Reasonable starting points, not scientifically derived:** the dislike and
regeneration deactivation thresholds (3), and the free-plan limit default
(3). All four are ordinary configuration/constants — tune them once you
have real distribution data on how often genuinely-bad mnemonics get
downvoted vs. regenerated.
