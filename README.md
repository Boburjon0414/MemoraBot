# MemoraBot

An AI-powered Telegram bot that helps English learners **permanently memorize
vocabulary** using mnemonics: for every English word, it finds Uzbek-sound
associations and wraps them in a short, funny, vivid story. The goal is
long-term memory, not translation.

This is Version 1: a small, deliberately-scoped feature set (registration +
the core MneVoca mnemonic flow), built on a clean architecture so the many
planned future features can be added without rewriting what's already here.

> **V1.1 (mnemonic engine quality pass):** rewrote the AI prompt for funnier,
> more natural, more memorable stories; redesigned the result message layout;
> added a global mnemonic cache so repeat words skip the AI call; added a
> "🔄 Generate Another Mnemonic" regenerate button; and added a 👍/👎 rating
> system backed by a new `mnemonic_feedback` table. No architecture changes —
> see §4 and §7 below for details. Same V1 feature scope otherwise.

> **V1.2 (knowledge-driven architecture + self-improving library):** the
> mnemonic prompt now lives entirely in `app/knowledge/` (versioned Markdown,
> assembled by a new Knowledge Engine) instead of Python code; difficulty
> moved to the CEFR scale (A1–C2); and `mnemonic_history` became a genuine
> self-improving library — the bot now serves the highest-rated *active*
> version of a word, auto-retires consistently poor versions, and tracks
> usage/response-time/regeneration stats. A configurable free-plan
> generation quota was added, and a read-only analytics data layer now
> exists (no dashboard yet). **Full documentation for all of this is in
> [`docs/`](docs/ARCHITECTURE.md)** — start there; this README covers V1/V1.1
> only below. Admin Panel, Premium/Subscription, Referral, and an Analytics
> dashboard were deliberately scoped out — see `docs/ROADMAP.md` for why and
> for the extension points already prepared for each.

---

## 1. Architecture

MemoraBot follows a strict layered architecture. Each layer only knows about
the layer directly below it:

```
Telegram
   │
   ▼
handlers/      thin aiogram glue: parses updates, calls a service, renders a reply
   │              no business logic lives here
   ▼
services/      business logic: registration, settings, mnemonic generation
   │              depends on repositories + the AIProvider abstraction
   ▼
repositories/  async data access, one class per entity, zero business logic
   │
   ▼
database/      SQLAlchemy models + engine/session setup (SQLite for V1)
```

A parallel, swappable branch hangs off the service layer:

```
services/mnemonic_service.py
   │  depends only on the abstract interface ↓
   ▼
services/ai/base.py  (AIProvider — abstract)
   │
   ├── services/ai/gemini_provider.py   (real implementation, calls Gemini)
   └── services/ai/mock_provider.py     (offline implementation, for dev/demo)
```

**How this maps to SOLID:**

| Principle | Where it shows up |
|---|---|
| **S**ingle Responsibility | Each handler/service/repository/keyboard file does exactly one thing |
| **O**pen/Closed | Add an `OpenAIProvider` by writing one new class — `MnemonicService` never changes |
| **L**iskov Substitution | `GeminiProvider` and `MockProvider` are fully interchangeable behind `AIProvider` |
| **I**nterface Segregation | Each repository only exposes methods its entity actually needs |
| **D**ependency Inversion | `MnemonicService` depends on `AIProvider` (abstract), never on `GeminiProvider` (concrete) |

**Dependency injection** happens in two small aiogram middlewares
(`app/middlewares/`): `DbSessionMiddleware` opens one `AsyncSession` per
Telegram update and commits/rolls it back automatically; `ServicesMiddleware`
builds the repositories and services for that session and injects them into
`data`. Handlers just declare a parameter like `user_service: UserService`
and aiogram passes in the ready-to-use instance — no external DI framework
needed at this scale.

---

## 2. Project Structure

```
memorabot/
├── run.py                     # Entry point: python run.py
├── requirements.txt
├── .env.example                # Copy to .env and fill in your values
├── alembic.ini / alembic/      # Schema migrations (see §5)
└── app/
    ├── bot.py                  # Composition root: wires everything together
    ├── config.py                # Pydantic Settings (reads .env)
    ├── logging_config.py
    │
    ├── core/                    # Shared enums + exceptions, zero dependencies
    ├── database/                 # SQLAlchemy base, engine/session, ORM models
    │   └── models/                # users, mnemonic_history, user_settings, mnemonic_feedback
    ├── repositories/              # Async data access, one file per entity
    ├── services/                  # Business logic
    │   └── ai/                     # AIProvider interface + Gemini/Mock implementations
    ├── middlewares/                # DB session + service dependency injection
    ├── states/                     # aiogram FSM state groups
    ├── keyboards/                  # Inline/reply keyboards + typed callback data
    ├── handlers/                   # Thin Telegram-facing glue code
    ├── texts/                      # uz/en/ru user-facing strings + t() helper
    └── utils/                      # Small stateless helpers (validation, formatting)
```

Every file is small and single-purpose on purpose — nothing here should ever
need to become a 500-line file as new features land.

---

## 3. Setup & Running

**Requirements:** Python 3.12+, a Telegram bot token from
[@BotFather](https://t.me/BotFather), optionally a
[Gemini API key](https://aistudio.google.com/apikey).

```bash
cd memorabot
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and set at least BOT_TOKEN

python run.py
```

That's it — on first launch MemoraBot automatically creates `memorabot.db`
and all three tables (see §5). If you leave `GEMINI_API_KEY` empty,
MneVoca still works end-to-end using the built-in `MockProvider`, so you can
try the whole flow before wiring up a real AI key.

---

## 4. How MneVoca Works (V1.1: cache, regenerate, rating)

1. User taps **🧠 MneVoca** on the dashboard → `handlers/mnevoca.py` sets the
   FSM state to `MneVocaStates.waiting_for_word` and prompts for a word.
2. User sends a word (e.g. `abandon`) → validated by
   `utils/validators.is_valid_english_word`.
3. `MnemonicService.get_or_generate()` checks the **mnemonic cache** first
   (`MnemonicRepository.get_latest_by_word`, a global lookup by word, not
   per-user). On a **cache hit**, the existing row is returned immediately —
   no AI call. On a **cache miss**, `AIProvider.generate_mnemonic()` is
   called — today that's `GeminiProvider`, calling Gemini's `generateContent`
   endpoint over `aiohttp` with `responseMimeType`/`responseSchema` set to
   `application/json`, so the model returns strict, parseable JSON.
4. The provider returns a validated `MnemonicResult` (word, meaning, Uzbek
   pronunciation similarity, mnemonic story, example sentence, difficulty).
   On a miss, this is saved as a new `mnemonic_history` row.
5. `MnemonicFeedbackService.get_user_rating()` checks whether the current
   viewer already rated this exact mnemonic, so the 👍/👎 buttons can show
   their existing choice with a ✅.
6. The handler formats the result with `utils/formatters.format_mnemonic_result`
   and sends it with **🔄 Generate Another Mnemonic**, **👍/👎**, **📝 New
   word**, and **🏠 Home** buttons.

**Regenerating** (🔄): `MnemonicService.regenerate()` skips the cache
entirely, collects every previous version's Uzbek pronunciation for that
word, and passes them to the AI provider as text it must explicitly avoid
repeating — then saves the result as a new row. Nothing is ever deleted;
the newest version simply becomes what future cache hits return.

**Rating** (👍/👎): `MnemonicFeedbackService.rate()` upserts a row in the new
`mnemonic_feedback` table, keyed by (mnemonic, user) — tapping the other
button later flips the same row instead of adding a duplicate.

---

## 5. Database & Migrations

V1 satisfies "auto-create the database on first launch" via
`app/database/session.py::init_models()`, which runs
`Base.metadata.create_all()` every time the bot starts — idempotent and safe,
no manual step required for a fresh install.

Alembic is fully scaffolded for when you need real migrations later (adding
a column, a new table, etc.) — V1.1's own `mnemonic_feedback` table is a
worked example, tracked as migration `0002` even though `create_all` also
picks it up automatically on next startup:

```bash
alembic stamp 0002                                   # run once, after first launch
alembic revision --autogenerate -m "add xyz column"   # for future changes
alembic upgrade head
```

The `alembic stamp` step matters: since the bot creates tables via
`create_all` rather than by running the migrations, Alembic doesn't otherwise
know the database is already at that baseline. Stamping tells it so, and
every future `--autogenerate` diff will be correct. (If you already stamped
at `0001` before this update, running `alembic stamp 0002` moves you to the
new baseline.)

---

## 6. Adding a New AI Provider

This is the architectural centerpiece of MemoraBot, so it's worth spelling
out explicitly:

1. Create `app/services/ai/openai_provider.py` implementing `AIProvider`
   (`name` property + `async generate_mnemonic(word) -> MnemonicResult`).
2. Add one branch to `app/services/ai/factory.py::create_ai_provider()`.
3. Done. `MnemonicService`, every handler, and the whole rest of the app
   never change, because they only ever depend on the abstract `AIProvider`.

---

## 7. Where Future Features Should Be Added

These are intentionally **not** part of V1 — the dashboard already reserves
their spots ("Coming Soon") so the UI won't need to change shape later.

- **Admin Panel** — new `app/handlers/admin/` package, gated by a filter
  checking `message.from_user.id in settings.admin_id_list` (already parsed
  and ready in `config.py`). Add repository methods for aggregate queries
  (user counts, popular words) rather than putting SQL in handlers.

- **Premium** — add a `subscriptions` table + `SubscriptionRepository` +
  `SubscriptionService`, plus a small aiogram filter/decorator
  (`@requires_premium`) that handlers can opt into, e.g. to gate word-count
  limits or unlock extra AI providers.

- **AI Chat** — new `ChatStates` FSM group, a `ChatService` that reuses the
  existing `AIProvider` abstraction with a conversational prompt (see
  `services/ai/prompts.py` for the pattern), and a `chat_history` table
  parallel to `mnemonic_history`.

- **Statistics** — `MnemonicRepository.get_recent_for_user()` and the new
  `mnemonic_feedback` table (👍/👎 per mnemonic, added in V1.1) are both
  ready to build on; add aggregate queries (words per day, streaks,
  helpful-rate per word/provider) and a new handler that renders them as
  text or a chart.

- **Spaced Repetition (SM-2)** — extend `mnemonic_history` with
  `next_review_at`, `review_count`, `ease_factor` columns (via a new Alembic
  migration), add a `ReviewService` implementing the SM-2 algorithm, and a
  background scheduler (e.g. APScheduler) that queries due reviews and
  messages users — `notifications_enabled` in `user_settings` is already in
  place for this.

---

## 8. Notes & Assumptions

- **Language:** the UI defaults to Uzbek and is fully localized (uz/en/ru)
  via `app/texts/messages.py::t()`; users can switch it from ⚙ Settings,
  which is why Settings is functional (not "Coming Soon") in V1.
- **MockProvider** isn't part of the original spec — it was added because it's
  the clearest possible demonstration of the "swap providers without touching
  business logic" requirement, and it means the project is runnable
  end-to-end with only a `BOT_TOKEN`, before you have a Gemini key.
- I wasn't able to `pip install` or live-run the bot against real Telegram/
  Gemini servers in the sandbox this was built in (no network access there).
  Every file was written against current, verified aiogram 3.29 / Gemini API
  documentation and checked for syntax validity, but please do a real test
  run (`python run.py`) before relying on it.
