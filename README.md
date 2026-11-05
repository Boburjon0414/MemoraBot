# MemoraBot

**An AI-powered Telegram learning assistant for English vocabulary, grammar, and practice.**

MemoraBot helps English learners build stronger recall and practise English in one Telegram bot. Its signature feature, **MneVoca**, creates mnemonic stories by connecting an English word to a similar-sounding Uzbek expression. The project also includes a personal vocabulary library, AI chat, AI-generated quizzes, channel-based grammar lessons, pronunciation audio, referrals, and an operational admin toolkit.

> **Project status:** This repository contains an actively evolving application. The feature list below distinguishes user-facing functionality that is wired into the bot from foundations that are present in the code but do not yet have a complete user-facing flow.

## What MemoraBot can do

### MneVoca: mnemonic vocabulary learning

- Accepts an English word and generates a structured learning entry with its meaning, an Uzbek-sound association, a short mnemonic story, an example sentence, and a CEFR-style difficulty label.
- Uses a versioned, Markdown-based knowledge base to guide mnemonic generation.
- Reuses the best active mnemonic already stored for a word instead of making a new AI request every time.
- Lets learners generate another version and rate a result with thumbs-up or thumbs-down feedback.
- Tracks usage, ratings, regeneration signals, provider, response time, and prompt version. Repeatedly regenerated-away versions can be retired from the active shared library.
- Automatically saves looked-up words to the learner's personal vocabulary.
- Applies a daily free-plan limit only to genuinely new AI generations. Cache hits do not consume the quota.

### Personal vocabulary

- Browse saved words and open their full mnemonic entries.
- Search the personal vocabulary list.
- Mark entries as favourites, review them, or delete them.
- Review a proposed system-generated update and accept or reject it.

### AI Chat

- Provides multi-turn English-learning conversations through the configured AI Gateway.
- Keeps chat-session history in the database and compresses older conversation turns into a short summary when the history grows beyond its configured threshold.
- Builds responses with relevant learner context, such as saved vocabulary, recent activity, learning goals, CEFR level, weak areas, and current topic when that information is available.
- Uses a lightweight, keyword-and-pattern-based planner to select relevant read-only data tools before sending a request to the model.
- Includes a response-validation step and a best-effort memory update hook. The current memory hook recognises a limited set of explicit English-language statements about CEFR level, learning goals, learning difficulties, and interests; it is not a general-purpose memory extractor.

### AI-generated quizzes

Quizzes are delivered as native Telegram Quiz Polls. Available modes in this code snapshot:

| Mode | What it practises |
|---|---|
| Vocabulary | Questions based on words in the learner's saved vocabulary. Requires at least three usable saved words. |
| Grammar | AI-generated questions on English grammar. |
| Gap-fill | Complete-the-sentence questions with answer options. |
| Reading | A short generated passage followed by comprehension questions. |
| Mixed | A combination of saved-vocabulary, grammar, and gap-fill questions. |
| Listening | Not implemented yet; the bot displays a “Coming Soon” message. |

Quiz generation uses learner context where available. Wrong answers can be recorded as weak areas for later personalisation. Question count and Telegram poll timing are configurable.

### Grammar lessons

- Presents a catalogue of grammar topics maintained by an administrator.
- Delivers lesson content by copying the corresponding post from a configured Telegram channel.
- Generates a quiz for the selected topic and tracks lesson opens, answers, accuracy, and a deterministic topic-mastery score.
- Includes an admin workflow to add topics from forwarded channel posts or message IDs, edit topic and button names, reorder topics, activate/deactivate entries, and remove topics.

The grammar catalogue is not bundled as a ready-made course: an operator must configure the channel and add the lesson topics.

### Pronunciation audio

Generates an English pronunciation voice message for a MneVoca word using `edge-tts`. The current handler uses the `en-US-JennyNeural` voice. This is a network-based text-to-speech feature, not an offline speech engine.

### Referrals and coins

- Generates personal referral links using Telegram deep-link payloads.
- Attributes a referral when a new user completes registration through an invite link.
- Awards coins using a configurable progressive reward formula with a maximum cap.
- Supports an optional welcome bonus for the new user.
- Shows a user's referral count, coin balance, and coin transaction history.
- Provides admin views for referral statistics, top referrers, top coin holders, recent referrals, and user referral/coin details.
- Allows administrators to add, remove, reset, or grant bonus coins to a user.

The code includes a configurable coin milestone that estimates progress toward a one-day Premium target. **This repository snapshot does not include a payment integration, a Premium purchase flow, or an automatic coin-to-Premium redemption flow.**

### Settings and localisation

- User interface translations are provided for Uzbek, English, and Russian.
- Learners can change the interface language and toggle the notification preference.
- New users register by sharing their own Telegram contact. The application stores the Telegram account ID, name, phone number, and username when available.

### Admin tools

The protected `/admin` command opens the application analytics panel. It includes an overview, most requested and most regenerated words, mnemonic quality rankings, AI-provider usage, prompt-version performance, and mnemonic-library growth.

Administrators can also:

- Send text-only broadcasts with a configurable delay between messages.
- Manage grammar lesson topics.
- Inspect AI Gateway health and key status.
- Enable/disable or pause/resume individual configured keys, test a key, enable/disable providers, change provider priority, and toggle maintenance mode.
- Review referral and coin-economy reports and perform supported coin adjustments.

Access is controlled by the numeric Telegram IDs configured in `ADMIN_IDS`.

## AI Gateway

The recommended runtime mode is `AI_PROVIDER=gateway`. The gateway currently supports **Google Gemini** and **Groq** and provides a shared routing path for mnemonic generation and generic AI requests used by AI Chat and quizzes.

Its implementation includes:

- Separate Free and Premium key pools for each provider.
- Round-robin key selection.
- Configurable model fallback order per provider.
- Key-health tracking, automatic cooldown after repeated failures, and recovery retries.
- Provider-priority fallback when a provider or its available keys cannot serve a request.
- Runtime provider/key controls and maintenance mode through the admin panel.
- Runtime operational settings persisted in `gateway_runtime.json` and applied without restarting the bot.

The Premium pool is a routing capability based on the user's stored Premium flag. It should not be confused with a completed subscription or payment system.

### Provider modes

| `AI_PROVIDER` | Behaviour |
|---|---|
| `gateway` | Recommended. Enables the multi-key Gemini/Groq gateway and the generic AI router used by AI Chat and quizzes. |
| `gemini` | Legacy single-key Gemini mode for the mnemonic-provider interface. |
| `groq` | Legacy single-key Groq mode for the mnemonic-provider interface. |
| `mock` | Deterministic development/demo provider; it does not provide real model responses. |

In gateway mode, configure at least one real key in `FREE_GEMINI_KEYS` or `FREE_GROQ_KEYS`. If no gateway keys are configured, startup falls back to `MockProvider`; MneVoca can still demonstrate its flow, but generic AI-router features such as AI Chat and AI-generated quizzes are unavailable in that fallback mode.

## How the application is structured

MemoraBot uses a layered, asynchronous architecture. Telegram handlers translate updates into service calls; services contain application logic; repositories isolate database access; and SQLAlchemy models define persistence.

```text
Telegram Bot (aiogram)
        |
        v
     handlers/  ---- keyboards/ + texts/
        |
        v
     services/
        |  \---- AIProvider / AIRouter
        |             |
        |             v
        |         AI Gateway
        |          |      |
        |        Gemini  Groq
        |
        +------ context/ + tools/
        +------ knowledge_engine/
        +------ content/ (infrastructure layer)
        |
        v
   repositories/
        |
        v
 SQLAlchemy models / database
```

Key design choices:

- **Dependency injection:** `DbSessionMiddleware` and `ServicesMiddleware` create request-scoped repositories/services and inject them into handlers.
- **Provider abstractions:** `MnemonicProvider` is scoped to mnemonic generation; `AIRouter` accepts generic AI requests. The gateway implements both interfaces so supported features share key pools, routing, and health management.
- **Versioned knowledge:** `app/knowledge/v1/`, `v2/`, and `v3/` store mnemonic instructions as Markdown, with YAML manifests defining prompt assembly. `MNEMONIC_PROMPT_VERSION` selects the active knowledge version.
- **Learner context:** `UserContextService` assembles available profile, vocabulary, streak, and learning-memory data. The planner selects relevant tools by message patterns and runs read-only lookups concurrently.
- **Persistence:** asynchronous SQLAlchemy 2.x data access, SQLite by default, and Alembic revision files for schema evolution.

Some files under `docs/` were written for earlier V1/V1.2 development stages and still contain historical planning notes that no longer match the current handlers and services. Treat the implementation described in this README and the current source code as authoritative until those design documents are reconciled.

## Technology stack

- Python 3.11+
- [aiogram 3](https://docs.aiogram.dev/) for the Telegram Bot API
- [SQLAlchemy 2](https://docs.sqlalchemy.org/) with async sessions
- [Alembic](https://alembic.sqlalchemy.org/) for database migrations
- [Pydantic Settings](https://docs.pydantic.dev/) for environment-based configuration
- `aiohttp` for asynchronous provider HTTP calls
- Google Gemini and Groq as supported AI providers
- `edge-tts` for pronunciation audio
- YAML and Markdown for versioned mnemonic knowledge files

## Getting started

### Prerequisites

- Python 3.11 or newer.
- A Telegram bot token created with [@BotFather](https://t.me/BotFather).
- At least one Gemini or Groq API key for real AI features.
- A Telegram channel for grammar lessons if you plan to use the Grammar module.

### 1. Clone the repository

```bash
git clone https://github.com/Boburjon0414/MemoraBot.git
cd MemoraBot
```

### 2. Create a virtual environment and install dependencies

**Windows PowerShell**

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Linux / macOS**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the sample file and edit it:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

At minimum, set:

```env
BOT_TOKEN=your_real_telegram_bot_token
AI_PROVIDER=gateway
FREE_GEMINI_KEYS=your_real_gemini_key
# or, instead:
# FREE_GROQ_KEYS=your_real_groq_key
```

Use comma-separated values to configure multiple keys. Do not commit `.env`, API keys, bot tokens, database files, or user data.

### 4. Start the bot

```bash
python run.py
```

The application creates missing database tables on startup. The repository also includes Alembic migrations under `alembic/versions/`; back up an existing database and review its current migration state before applying schema upgrades.

### 5. Optional configuration

| Variable | Purpose | Default / note |
|---|---|---|
| `DATABASE_URL` | Async SQLAlchemy database URL | `sqlite+aiosqlite:///./memorabot.db` |
| `MNEMONIC_PROMPT_VERSION` | Selects `app/knowledge/<version>/` | `v1` in code; `v3` is included in the supplied sample configuration |
| `FREE_PLAN_DAILY_GENERATIONS` | New MneVoca AI generations per 24-hour window for free users | `3`; cached words are free |
| `FREE_GEMINI_KEYS` / `FREE_GROQ_KEYS` | Comma-separated Free-tier gateway keys | At least one real key is needed for real AI calls |
| `PREMIUM_GEMINI_KEYS` / `PREMIUM_GROQ_KEYS` | Comma-separated Premium-tier keys | Optional; only used for users whose Premium flag is enabled |
| `GEMINI_MODELS` / `GROQ_MODELS` | Models to try for each provider, in order | See `app/config.py` |
| `GATEWAY_PROVIDER_PRIORITY` | Provider order | `gemini,groq` |
| `ADMIN_IDS` | Comma-separated numeric Telegram user IDs | Leave blank to disable admin access |
| `BOT_USERNAME` | Bot username without `@`, used for invite links | Set this to the deployed bot's username |
| `GRAMMAR_CHANNEL_ID` | Telegram channel ID containing lesson posts | `0` disables channel-backed lessons until configured |
| `QUIZ_OPEN_PERIOD` | Duration of quiz polls, in seconds | `20`; `0` disables the timer |
| `GRAMMAR_QUIZ_QUESTIONS` | Questions per grammar quiz | `5` |
| `GRAMMAR_QUIZ_TIME_SECONDS` | Grammar poll timer | `20` |
| `QUIZ_VOCABULARY_QUESTIONS` | Questions in a vocabulary quiz | `5`, adjusted to available saved words |
| `BROADCAST_DELAY_MS` | Delay between broadcast messages | `50` |
| `LOG_LEVEL` | Application log level | `INFO` |

See `app/config.py` for the full list of supported settings. Unknown environment variables are ignored by the settings model, so use the exact names shown there.

## Setting up the Grammar module

1. Create a Telegram channel for lesson posts.
2. Add the bot to that channel with permission to access and copy the lesson messages.
3. Set `GRAMMAR_CHANNEL_ID` to the channel's numeric ID.
4. Add your Telegram user ID to `ADMIN_IDS`.
5. Open `/admin` and use the Grammar Topics controls to add lesson topics by forwarding a channel post or entering its message ID.

The lesson content itself remains in the Telegram channel; MemoraBot stores topic metadata and the source message ID.

## Current implementation boundaries

The following distinctions are important when evaluating the repository:

- The **Statistics** button on the learner dashboard is still a Coming Soon screen. Learning activity is recorded and used in learner context, and the separate admin analytics reports are implemented.
- **Listening quizzes** are a Coming Soon screen.
- The **Premium payment/subscription journey** is not implemented. The code has a Premium flag, separate gateway key pools, and coin milestone calculations, but no checkout or automatic activation flow.
- The content/document subsystem has database models, a plain-text processor, chunking, and an embedding-store abstraction. In this snapshot the platform uses a deterministic `MockEmbedder`, only the plain-text processor is registered, and there is no user-facing document-upload workflow or production semantic-embedding integration. It should be treated as groundwork, not a finished document-RAG feature.
- Flashcard, summary, and presentation payload/tool abstractions exist for future extension, but this snapshot does not include complete user-facing generators for those features.
- The supplied ZIP does not contain a `tests/` directory or an automated test suite. Python source files were syntax-parsed during this review, but that is not a substitute for integration testing with Telegram and live AI-provider credentials.

## Data and privacy considerations

MemoraBot stores Telegram account identifiers and profile details, including the phone number shared during registration. It also stores user settings, vocabulary entries, mnemonic feedback, learning activity, quiz/chat output, and selected learning-profile fields. AI-powered interactions send the relevant prompt and message content to the configured external provider (Gemini or Groq).

Anyone deploying the bot for real learners should publish a privacy notice, explain the use of third-party AI providers, protect the database and runtime configuration files, and define an appropriate data-retention/deletion process. Do not use real user data in public issue reports or example fixtures.

## Repository layout

```text
.
├── app/
│   ├── handlers/          # Telegram update handlers
│   ├── keyboards/         # Inline and reply keyboards
│   ├── texts/             # Uzbek, English, and Russian interface strings
│   ├── services/          # Application and domain services
│   │   ├── ai/            # Providers, gateway, knowledge engine
│   │   ├── context/       # Learner context and prompt construction
│   │   ├── content/       # Text processing and indexing foundations
│   │   ├── outputs/       # Structured output schemas
│   │   └── tools/         # Context lookup tools and planner
│   ├── repositories/      # Async database access
│   ├── database/models/   # SQLAlchemy models
│   ├── middlewares/       # Session and service injection
│   ├── knowledge/         # Versioned mnemonic knowledge bases
│   └── platform/         # Application-lifetime resources
├── alembic/               # Database migration environment and revisions
├── docs/                  # Architecture and feature design notes
├── gateway_runtime.json   # Non-secret runtime gateway controls
├── requirements.txt
├── .env.example
└── run.py                 # Application entry point
```

## License

No `LICENSE` file was included in the supplied project snapshot. Until a license is added, the repository does not grant an explicit license to reuse, modify, or redistribute the code. Add the license you choose before presenting the project as a formally licensed open-source project.
