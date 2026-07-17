# Roadmap: What's Built, What's Proposed, and Why

The original brief for this phase of work spanned a knowledge engine, a
self-improving mnemonic library, a free-plan quota, analytics, an admin
panel (with photo/video broadcast), a premium/subscription system with
expiration, and a referral system. This document explains exactly what got
built now, what's deliberately deferred, and why — so a future session
doesn't have to re-derive the reasoning or accidentally duplicate work.

## Why not build everything in one pass

Three concrete reasons, not general caution:

1. **This sandbox has no network access.** Nothing that depends on
   aiogram/SQLAlchemy could be executed, only syntax-checked and
   cross-referenced. The pieces that *were* built this phase were chosen
   partly because they could be genuinely tested in isolation (the
   Knowledge Engine, the migration SQL against a real database copy, the
   rating/deactivation business logic against fake repositories) — see
   `docs/ARCHITECTURE.md`, "What was actually tested." A feature like
   broadcast messaging to every user has no equivalent safe way to verify
   without a live bot and real Telegram accounts.
2. **Several deferred features need a product decision, not an
   implementation default.** Which payment rail funds Premium (Telegram
   Stars? Click? Payme? a manual admin toggle)? What counts as "expiration"
   without payments? What's the Admin Panel's intended surface — commands
   inside Telegram, or a separate web dashboard? Guessing these and
   building on the guess risks throwing the work away.
3. **Reviewability.** A smaller, complete, verified change is easier to
   trust and easier to roll back than one enormous diff touching a dozen
   new subsystems at once.

## Built now (Phase 1)

- Knowledge Engine (`docs/KNOWLEDGE_ENGINE.md`)
- Self-improving mnemonic library: rating-based serving, auto-deactivation,
  regeneration tracking, response-time tracking (`docs/MNEMONIC_LIBRARY.md`)
- Free-plan generation quota, configurable limit
- **Analytics data layer** (`AnalyticsRepository` + `AnalyticsService`) —
  see below; the queries exist and are correct, but nothing displays them yet

## Analytics: data layer built, dashboard deferred

Every method below is implemented, in `app/repositories/analytics_repository.py`
and wrapped by `app/services/analytics_service.py`, but **not called from
any handler** — there's no Admin Panel yet to call it from.

| Method | Answers |
|---|---|
| `total_users` | Total registered users |
| `total_unique_words` / `total_mnemonic_versions` | Library size |
| `active_vs_deactivated_counts` | How much content has been auto-retired |
| `most_requested_words` | Highest total `uses`, summed per word |
| `most_regenerated_words` | Words the knowledge base struggles with |
| `highest_rated_active` / `lowest_rated_active` | Best/worst performing content |
| `ai_provider_usage` | Breakdown by provider (relevant once a 2nd provider exists) |
| `prompt_version_performance` | Average rating per knowledge-base version |
| `average_response_time_ms` | Gemini latency, excluding cache hits |
| `library_growth_by_day` | New versions created per day |

**Not built:** Daily/Weekly/Monthly active users, Premium vs. Free user
counts, Most Active Users, Gemini token usage, User Feedback Trends (as a
time series), Top Difficult Words. DAU/WAU/MAU needs a definition of
"active" (opened the bot? sent a message? generated a word?) that's a
product decision. Token usage needs the Gemini response's `usageMetadata`
to be captured and stored — a small, well-contained addition to
`GeminiProvider` + a new column, straightforward to add once there's a
dashboard that would use it. Premium/Free counts need Premium to exist
first (see below).

**When the Admin Panel UI exists**, it should be a presentation layer over
this exact data layer — no new queries needed for anything in the table
above.

## Admin Panel: deferred

Needs, before implementation makes sense:
- **Auth model decision.** `settings.admin_id_list` already exists
  (parsed, unused) as the natural gate for a Telegram-based admin UI. If a
  separate web dashboard is wanted instead, that's a different tech stack
  entirely and should be decided explicitly.
- **Broadcast messaging (text/photo/video/buttons) is operationally
  risky to build speculatively.** Telegram rate-limits aggressively; a
  broadcast-to-all-users feature needs batching, backoff, and a
  confirmation flow to avoid an accidental mass-send or a bot-wide
  rate-limit ban. This deserves a focused pass with real testing against
  a live bot, not a guess bundled into a larger change.

**Suggested shape when built:** `app/handlers/admin/` package, gated by a
filter checking `message.from_user.id in settings.admin_id_list`, calling
into `AnalyticsService` (already built) for the dashboard, and a new,
carefully-throttled `BroadcastService` for messaging.

## Premium / Subscription: deferred

Needs a payment integration decision first (see above). Suggested shape
once decided: a `subscriptions` table (`user_id`, `plan`, `expires_at`,
`payment_reference`), a `SubscriptionService`, and a one-line change to
`UsageService.has_quota_remaining` to bypass the free-plan limit for active
subscribers. The quota system was deliberately built so this bypass is the
*only* change needed there.

## Referral System: deferred

Depends on the free-plan quota existing first (done). Suggested shape: a
`referrals` table (`referrer_user_id`, `referred_user_id`, `created_at`),
using Telegram's `/start <payload>` deep-linking to attribute a new
registration to whoever's link they used, and a reward rule (e.g. +3 bonus
generations per successful referral, itself just an addition to the same
`user_settings` counter `UsageService` already reads).

## The two still-empty knowledge files

`EVALUATION_GUIDE.md` and `TEST_CASES.md` (in `app/knowledge/v1/`) were
left empty rather than populated with invented content, because:
- They're not part of what's sent to the AI (see `PROMPT_FRAMEWORK.md`),
  so leaving them empty doesn't affect generation quality today.
- `EVALUATION_GUIDE.md`'s purpose (a rubric for judging mnemonic quality —
  for a human reviewer, or eventually an automated LLM-as-judge pass) and
  `TEST_CASES.md`'s purpose (concrete regression scenarios) both benefit
  from real examples of mnemonics that *did* and *didn't* work well in
  production — which only exist once the bot has been used enough to
  generate that history. Writing them now would mean inventing plausible-
  sounding but ultimately fabricated content.
- The Knowledge Engine's validator explicitly does not require
  `reference_only` files to be non-empty (see `docs/KNOWLEDGE_ENGINE.md`),
  so there's no technical reason to fill them prematurely.

## Multi-provider expansion (Claude, OpenAI, local GGUF)

Architecturally ready today — see `docs/KNOWLEDGE_ENGINE.md`, "Adding a new
AI provider." Not built because no second provider was requested
concretely; the brief asked for the *capability*, which already exists and
needs no further work to demonstrate (`MockProvider` already proves a
second, fully interchangeable implementation of `AIProvider` works
end-to-end).
