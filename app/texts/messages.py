"""All user-facing strings in Uzbek (uz), English (en), and Russian (ru).

V1.5 i18n migration:
  - All existing keys are PRESERVED and UNCHANGED (backward compatible).
  - New keys follow dot-notation naming (e.g. "admin.btn.overview").
  - Every key has all three languages — no missing translations.
  - `t()` fallback order: requested lang → English → Uzbek → raw key.
    (Updated per spec: "If a user has an invalid language, fallback to English.")

Key namespaces added:
  admin.*          — admin panel, menus, reports, broadcast
  admin.referral.* — admin referral control panel
  referral.*       — user-facing referral / invite page
  coins.*          — coin history page
  gateway.*        — AI gateway admin panel
  common.*         — shared micro-strings
"""

from __future__ import annotations

from typing import Final

MESSAGES: Final[dict[str, dict[str, str]]] = {
    # ────────────────────────────────────────────────────────────────────────
    # EXISTING KEYS — DO NOT RENAME, DELETE, OR CHANGE (backward-compatible)
    # ────────────────────────────────────────────────────────────────────────
    "welcome_new": {
        "uz": (
            "Assalomu alaykum, {name}! 👋\n\n"
            "Men MemoraBot — ingliz tilidagi so'zlarni uzoq muddatli xotirada saqlab qolishga "
            "yordam beruvchi sun'iy intellekt botiman.\n\n"
            "Ro'yxatdan o'tish uchun quyidagi tugma orqali kontakt ma'lumotingizni ulashing 👇"
        ),
        "en": (
            "Hello, {name}! 👋\n\n"
            "I'm MemoraBot — an AI bot that helps you memorize English words for the long term.\n\n"
            "To register, please share your contact using the button below 👇"
        ),
        "ru": (
            "Здравствуйте, {name}! 👋\n\n"
            "Я MemoraBot — ИИ-бот, который помогает надолго запоминать английские слова.\n\n"
            "Чтобы зарегистрироваться, поделитесь контактом с помощью кнопки ниже 👇"
        ),
    },
    "welcome_back": {
        "uz": "Yana xush kelibsiz, {name}! 👋",
        "en": "Welcome back, {name}! 👋",
        "ru": "С возвращением, {name}! 👋",
    },
    "share_contact_button": {
        "uz": "📱 Kontaktni ulashish",
        "en": "📱 Share Contact",
        "ru": "📱 Поделиться контактом",
    },
    "contact_invalid": {
        "uz": "❗️ Iltimos, faqat o'zingizning kontaktingizni ulashing.",
        "en": "❗️ Please share only your own contact.",
        "ru": "❗️ Пожалуйста, поделитесь только своим собственным контактом.",
    },
    "contact_prompt_retry": {
        "uz": "Iltimos, pastdagi tugma orqali kontaktingizni ulashing 👇",
        "en": "Please share your contact using the button below 👇",
        "ru": "Пожалуйста, поделитесь контактом с помощью кнопки ниже 👇",
    },
    "registration_success": {
        "uz": "✅ Rahmat, {name}! Siz muvaffaqiyatli ro'yxatdan o'tdingiz.",
        "en": "✅ Thank you, {name}! You have registered successfully.",
        "ru": "✅ Спасибо, {name}! Вы успешно зарегистрированы.",
    },
    "dashboard_title": {
        "uz": "🏠 <b>Bosh sahifa</b>\n\nQuyidagi bo'limlardan birini tanlang:",
        "en": "🏠 <b>Home</b>\n\nChoose one of the sections below:",
        "ru": "🏠 <b>Главная</b>\n\nВыберите один из разделов ниже:",
    },
    "coming_soon": {
        "uz": "🚧 Bu bo'lim tez orada ishga tushadi. Kuzatib boring!",
        "en": "🚧 This section is coming soon. Stay tuned!",
        "ru": "🚧 Этот раздел скоро появится. Следите за обновлениями!",
    },
    "btn_mnevoca": {"uz": "🧠 MneVoca", "en": "🧠 MneVoca", "ru": "🧠 MneVoca"},
    "btn_ai_chat": {
        "uz": "🤖 AI Suhbat (Tez orada)",
        "en": "🤖 AI Chat (Coming Soon)",
        "ru": "🤖 ИИ-чат (Скоро)",
    },
    "btn_statistics": {
        "uz": "📊 Statistika (Tez orada)",
        "en": "📊 Statistics (Coming Soon)",
        "ru": "📊 Статистика (Скоро)",
    },
    "btn_settings": {"uz": "⚙ Sozlamalar", "en": "⚙ Settings", "ru": "⚙ Настройки"},
    "btn_about": {"uz": "ℹ Bot haqida", "en": "ℹ About", "ru": "ℹ О боте"},
    "btn_invite_friends": {
        "uz": "👥 Do'stlarni taklif qiling",
        "en": "👥 Invite Friends",
        "ru": "👥 Пригласить друзей",
    },
    "btn_back_home": {"uz": "🏠 Bosh sahifa", "en": "🏠 Home", "ru": "🏠 Главная"},
    "btn_another_word": {
        "uz": "📝 Yangi so'z",
        "en": "📝 New word",
        "ru": "📝 Новое слово",
    },
    "mnevoca_prompt": {
        "uz": (
            "🧠 <b>MneVoca</b>\n\nEslab qolishni istagan ingliz tilidagi so'zni yuboring.\n\n"
            "Masalan: <code>abandon</code>"
        ),
        "en": (
            "🧠 <b>MneVoca</b>\n\nSend an English word you'd like to memorize.\n\n"
            "Example: <code>abandon</code>"
        ),
        "ru": (
            "🧠 <b>MneVoca</b>\n\nОтправьте английское слово, которое хотите запомнить.\n\n"
            "Например: <code>abandon</code>"
        ),
    },
    "mnevoca_generating": {
        "uz": "🧠 Xotira hikoyasi tayyorlanmoqda... ⏳",
        "en": "🧠 Preparing your memory story... ⏳",
        "ru": "🧠 Готовим историю для запоминания... ⏳",
    },
    "mnevoca_invalid_word": {
        "uz": "❗️ Iltimos, faqat lotin harflaridan iborat bitta ingliz so'zini yuboring.",
        "en": "❗️ Please send a single English word using Latin letters only.",
        "ru": "❗️ Пожалуйста, отправьте одно английское слово латинскими буквами.",
    },
    "mnevoca_error": {
        "uz": "😔 Uzr, hozircha bu so'z uchun hikoya tayyorlab bo'lmadi. Birozdan so'ng qaytadan urinib ko'ring.",
        "en": "😔 Sorry, this word's story couldn't be generated right now. Please try again shortly.",
        "ru": "😔 Извините, не удалось составить историю для этого слова. Попробуйте немного позже.",
    },
    "free_plan_limit_reached": {
        "uz": (
            "🚫 Siz bugungi bepul limitga ({limit} ta yangi so'z) yetdingiz.\n\n"
            "Limit 24 soatdan so'ng avtomatik tiklanadi.\n"
            "Kutubxonada mavjud so'zlarni esa istalgancha bepul ko'rishingiz mumkin — "
            "limit faqat botimiz hali ko'rmagan, yangi AI orqali yaratiladigan so'zlarga tegishli."
        ),
        "en": (
            "🚫 You've reached today's free plan limit of {limit} new AI-generated words.\n\n"
            "Your quota resets automatically after 24 hours.\n"
            "You can still look up any word already in the library for free — the limit only "
            "applies to genuinely new words that require a fresh AI generation."
        ),
        "ru": (
            "🚫 Вы исчерпали дневной лимит бесплатного плана: {limit} новых слов.\n\n"
            "Лимит автоматически обновится через 24 часа.\n"
            "Слова, уже имеющиеся в библиотеке, по-прежнему доступны бесплатно — "
            "лимит касается только полностью новых слов, требующих обращения к ИИ."
        ),
    },
    "btn_regenerate": {
        "uz": "🔄 Qayta tuzish",
        "en": "🔄 Regenerate",
        "ru": "🔄 Регенерировать"
    },
    "btn_pronunciation": {
        "uz": "🔊 Talaffuz",
        "en": "🔊 Pronunciation",
        "ru": "🔊 Произношение",
    },
    "pron_cap": {
        "uz": "@TryMemoraBot orqali tezroq o'rganing!",
        "en": "Learn faster with @TryMemoraBot!",
        "ru": "Учите быстрее с @TryMemoraBot!",
    },
    "btn_helpful": {"uz": "👍 Foydali", "en": "👍 Helpful", "ru": "👍 Полезно"},
    "btn_helpful_selected": {
        "uz": "👍 Foydali ✅",
        "en": "👍 Helpful ✅",
        "ru": "👍 Полезно ✅",
    },
    "btn_not_helpful": {"uz": "👎 Foydasiz", "en": "👎 Not Helpful", "ru": "👎 Не полезно"},
    "btn_not_helpful_selected": {
        "uz": "👎 Foydasiz ✅",
        "en": "👎 Not Helpful ✅",
        "ru": "👎 Не полезно ✅",
    },
    "rating_thanks": {
        "uz": "Rahmat! Fikringiz saqlandi.",
        "en": "Thanks! Your feedback was saved.",
        "ru": "Спасибо! Ваш отзыв сохранён.",
    },
    "settings_title": {
        "uz": "⚙ <b>Sozlamalar</b>\n\nBot tilini yoki bildirishnomalarni shu yerdan boshqarishingiz mumkin:",
        "en": "⚙ <b>Settings</b>\n\nManage the bot's language and notifications here:",
        "ru": "⚙ <b>Настройки</b>\n\nЗдесь можно изменить язык бота и уведомления:",
    },
    "settings_language_updated": {
        "uz": "✅ Til muvaffaqiyatli o'zgartirildi.",
        "en": "✅ Language updated successfully.",
        "ru": "✅ Язык успешно изменён.",
    },
    "btn_notifications_on": {
        "uz": "🔔 Bildirishnomalar: yoqilgan",
        "en": "🔔 Notifications: on",
        "ru": "🔔 Уведомления: включены",
    },
    "btn_notifications_off": {
        "uz": "🔕 Bildirishnomalar: o'chirilgan",
        "en": "🔕 Notifications: off",
        "ru": "🔕 Уведомления: выключены",
    },
    "about_text": {
        "uz": (
            "ℹ️ <b>MemoraBot</b> — v1.0.0\n\n"
            "MemoraBot — ingliz tilidagi so'zlarni mnemonika usulida, ya'ni o'zbekcha tovush "
            "assotsiatsiyalari va qiziqarli hikoyalar orqali uzoq muddatli xotirada saqlashga "
            "yordam beruvchi sun'iy intellekt botidir.\n\n"
            "Maqsad — tarjima emas, balki chinakam eslab qolish."
        ),
        "en": (
            "ℹ️ <b>MemoraBot</b> — v1.0.0\n\n"
            "MemoraBot is an AI bot that helps you permanently memorize English words using "
            "mnemonics — Uzbek sound associations paired with vivid stories.\n\n"
            "The goal is genuine long-term memory, not translation."
        ),
        "ru": (
            "ℹ️ <b>MemoraBot</b> — v1.0.0\n\n"
            "MemoraBot — это ИИ-бот, который помогает надолго запоминать английские слова с "
            "помощью мнемотехники: звуковых ассоциаций с узбекским языком и ярких историй.\n\n"
            "Цель — настоящее запоминание, а не перевод."
        ),
    },
    "error_generic": {
        "uz": "😔 Kutilmagan xatolik yuz berdi. Iltimos, birozdan so'ng qaytadan urinib ko'ring.",
        "en": "😔 An unexpected error occurred. Please try again shortly.",
        "ru": "😔 Произошла непредвиденная ошибка. Попробуйте немного позже.",
    },
    "prompt_use_start": {
        "uz": "Boshlash uchun /start buyrug'ini yuboring.",
        "en": "Please send /start to begin.",
        "ru": "Пожалуйста, отправьте /start, чтобы начать.",
    },
    "label_meaning": {"uz": "Ma'nosi", "en": "Meaning", "ru": "Значение"},
    "label_pronunciation": {
        "uz": "O'zbekcha talaffuz o'xshashligi",
        "en": "Uzbek pronunciation similarity",
        "ru": "Схожесть произношения с узбекским",
    },
    "label_story": {"uz": "Xotira hikoyasi", "en": "Memory story", "ru": "История для запоминания"},
    "label_example": {"uz": "Misol", "en": "Example", "ru": "Пример"},
    "label_difficulty": {"uz": "Qiyinlik darajasi", "en": "Difficulty", "ru": "Сложность"},
    "difficulty_a1": {"uz": "🟢 A1 — Boshlang'ich", "en": "🟢 A1 — Beginner", "ru": "🟢 A1 — Начальный"},
    "difficulty_a2": {"uz": "🟢 A2 — Elementar", "en": "🟢 A2 — Elementary", "ru": "🟢 A2 — Элементарный"},
    "difficulty_b1": {
        "uz": "🟡 B1 — O'rta darajadan past",
        "en": "🟡 B1 — Intermediate",
        "ru": "🟡 B1 — Средний",
    },
    "difficulty_b2": {
        "uz": "🟡 B2 — O'rta darajadan yuqori",
        "en": "🟡 B2 — Upper-Intermediate",
        "ru": "🟡 B2 — Выше среднего",
    },
    "difficulty_c1": {"uz": "🔴 C1 — Yuqori", "en": "🔴 C1 — Advanced", "ru": "🔴 C1 — Продвинутый"},
    "difficulty_c2": {"uz": "🔴 C2 — Mukammal", "en": "🔴 C2 — Proficient", "ru": "🔴 C2 — В совершенстве"},

    # ────────────────────────────────────────────────────────────────────────
    # COMMON — shared micro-strings
    # ────────────────────────────────────────────────────────────────────────
    "common.default_name": {"uz": "do'stim", "en": "friend", "ru": "друг"},
    "common.no_data": {
        "uz": "Hali ma'lumot yo'q.",
        "en": "No data yet.",
        "ru": "Данных пока нет.",
    },
    "common.yes": {"uz": "Ha", "en": "Yes", "ru": "Да"},
    "common.no": {"uz": "Yo'q", "en": "No", "ru": "Нет"},

    # ────────────────────────────────────────────────────────────────────────
    # ADMIN — core
    # ────────────────────────────────────────────────────────────────────────
    "admin.denied": {
        "uz": "⛔ Sizda admin panelga kirish huquqi yo'q.",
        "en": "⛔ You do not have access to the admin panel.",
        "ru": "⛔ У вас нет доступа к панели администратора.",
    },
    "admin.denied_callback": {
        "uz": "⛔ Bu bo'lim faqat administratorlar uchun.",
        "en": "⛔ This section is for administrators only.",
        "ru": "⛔ Этот раздел только для администраторов.",
    },
    "admin.overview.title": {
        "uz": "🔐 <b>Admin panel · Statistika</b>",
        "en": "🔐 <b>Admin Panel · Statistics</b>",
        "ru": "🔐 <b>Панель администратора · Статистика</b>",
    },
    "admin.overview.subtitle": {
        "uz": "<i>MemoraBot kutubxonasining umumiy holati</i>",
        "en": "<i>MemoraBot library overall status</i>",
        "ru": "<i>Общее состояние библиотеки MemoraBot</i>",
    },
    "admin.overview.users": {
        "uz": "👤 Foydalanuvchilar: <b>{value}</b>",
        "en": "👤 Users: <b>{value}</b>",
        "ru": "👤 Пользователи: <b>{value}</b>",
    },
    "admin.overview.words": {
        "uz": "📚 Noyob so'zlar: <b>{value}</b>",
        "en": "📚 Unique words: <b>{value}</b>",
        "ru": "📚 Уникальных слов: <b>{value}</b>",
    },
    "admin.overview.mnemonics": {
        "uz": "🧠 Mnemonika versiyalari: <b>{value}</b>",
        "en": "🧠 Mnemonic versions: <b>{value}</b>",
        "ru": "🧠 Версий мнемоник: <b>{value}</b>",
    },
    "admin.overview.active": {
        "uz": "✅ Faol versiyalar: <b>{value}</b>",
        "en": "✅ Active versions: <b>{value}</b>",
        "ru": "✅ Активных версий: <b>{value}</b>",
    },
    "admin.overview.deactivated": {
        "uz": "🗄 Faolsizlantirilgan: <b>{value}</b>",
        "en": "🗄 Deactivated: <b>{value}</b>",
        "ru": "🗄 Деактивировано: <b>{value}</b>",
    },
    "admin.overview.avg_response": {
        "uz": "⚡ O'rtacha AI javob vaqti: <b>{value} ms</b>",
        "en": "⚡ Average AI response time: <b>{value} ms</b>",
        "ru": "⚡ Среднее время ответа ИИ: <b>{value} мс</b>",
    },
    "admin.overview.footer": {
        "uz": "Kerakli hisobotni pastdagi menyudan tanlang.",
        "en": "Select the report you need from the menu below.",
        "ru": "Выберите нужный отчёт из меню ниже.",
    },

    # ────────────────────────────────────────────────────────────────────────
    # ADMIN — menu buttons
    # ────────────────────────────────────────────────────────────────────────
    "admin.btn.overview": {
        "uz": "📊 Umumiy ko'rinish",
        "en": "📊 Overview",
        "ru": "📊 Обзор",
    },
    "admin.btn.requested": {
        "uz": "🔥 Eng ko'p so'ralgan",
        "en": "🔥 Most Requested",
        "ru": "🔥 Наиболее запрашиваемые",
    },
    "admin.btn.regenerated": {
        "uz": "🔄 Qayta yaratilgan",
        "en": "🔄 Most Regenerated",
        "ru": "🔄 Наиболее перегенерированные",
    },
    "admin.btn.quality": {
        "uz": "⭐ Sifat reytingi",
        "en": "⭐ Quality Rating",
        "ru": "⭐ Рейтинг качества",
    },
    "admin.btn.ai": {
        "uz": "🤖 AI va promptlar",
        "en": "🤖 AI & Prompts",
        "ru": "🤖 ИИ и промпты",
    },
    "admin.btn.growth": {
        "uz": "📈 Kutubxona o'sishi",
        "en": "📈 Library Growth",
        "ru": "📈 Рост библиотеки",
    },
    "admin.btn.referral": {
        "uz": "👥 Referral boshqaruvi",
        "en": "👥 Referral Management",
        "ru": "👥 Управление рефералами",
    },
    "admin.btn.broadcast": {
        "uz": "📢 Xabar tarqatish",
        "en": "📢 Broadcast",
        "ru": "📢 Рассылка",
    },
    "admin.btn.gateway": {
        "uz": "🤖 AI Gateway boshqaruvi",
        "en": "🤖 AI Gateway Control",
        "ru": "🤖 Управление AI Gateway",
    },
    "admin.btn.close": {
        "uz": "✖️ Yopish",
        "en": "✖️ Close",
        "ru": "✖️ Закрыть",
    },
    "admin.btn.back": {
        "uz": "⬅️ Admin menyu",
        "en": "⬅️ Admin Menu",
        "ru": "⬅️ Меню администратора",
    },

    # ────────────────────────────────────────────────────────────────────────
    # ADMIN — report pages
    # ────────────────────────────────────────────────────────────────────────
    "admin.most_requested.title": {
        "uz": "🔥 <b>Eng ko'p so'ralgan 10 ta so'z</b>",
        "en": "🔥 <b>Top 10 Most Requested Words</b>",
        "ru": "🔥 <b>Топ 10 наиболее запрашиваемых слов</b>",
    },
    "admin.most_requested.unit": {
        "uz": "jami ko'rishlar",
        "en": "total views",
        "ru": "всего просмотров",
    },
    "admin.most_regenerated.title": {
        "uz": "🔄 <b>Eng ko'p qayta yaratilgan 10 ta so'z</b>",
        "en": "🔄 <b>Top 10 Most Regenerated Words</b>",
        "ru": "🔄 <b>Топ 10 наиболее перегенерированных слов</b>",
    },
    "admin.most_regenerated.unit": {
        "uz": "qayta yaratishlar",
        "en": "regenerations",
        "ru": "перегенераций",
    },
    "admin.word_ranking.unit_label": {
        "uz": "Qiymatlar: {unit}",
        "en": "Values: {unit}",
        "ru": "Значения: {unit}",
    },
    "admin.quality.title": {
        "uz": "⭐ <b>Sifat reytingi</b>",
        "en": "⭐ <b>Quality Rating</b>",
        "ru": "⭐ <b>Рейтинг качества</b>",
    },
    "admin.quality.best": {
        "uz": "🏆 <b>Eng yaxshi faol versiyalar</b>",
        "en": "🏆 <b>Best Active Versions</b>",
        "ru": "🏆 <b>Лучшие активные версии</b>",
    },
    "admin.quality.worst": {
        "uz": "⚠️ <b>E'tibor talab qiladigan faol versiyalar</b>",
        "en": "⚠️ <b>Active Versions Needing Attention</b>",
        "ru": "⚠️ <b>Активные версии, требующие внимания</b>",
    },
    "admin.quality.note": {
        "uz": "<i>Reyting: (like − dislike) / jami baholar</i>",
        "en": "<i>Rating: (likes − dislikes) / total ratings</i>",
        "ru": "<i>Рейтинг: (лайки − дизлайки) / всего оценок</i>",
    },
    "admin.quality.views_unit": {
        "uz": "ko'rish",
        "en": "views",
        "ru": "просм.",
    },
    "admin.ai.title": {
        "uz": "🤖 <b>AI va promptlar samaradorligi</b>",
        "en": "🤖 <b>AI & Prompt Efficiency</b>",
        "ru": "🤖 <b>Эффективность ИИ и промптов</b>",
    },
    "admin.ai.providers_header": {
        "uz": "<b>Providerlar bo'yicha yaratilgan versiyalar</b>",
        "en": "<b>Versions Generated by Provider</b>",
        "ru": "<b>Версии по провайдеру</b>",
    },
    "admin.ai.prompts_header": {
        "uz": "<b>Prompt versiyalari bo'yicha natija</b>",
        "en": "<b>Results by Prompt Version</b>",
        "ru": "<b>Результаты по версии промпта</b>",
    },
    "admin.ai.prompt_entry": {
        "uz": "• <b>{version}</b> — {count} versiya, o'rtacha reyting {rating}",
        "en": "• <b>{version}</b> — {count} versions, average rating {rating}",
        "ru": "• <b>{version}</b> — {count} версий, средний рейтинг {rating}",
    },
    "admin.growth.title": {
        "uz": "📈 <b>Oxirgi 30 kun: kutubxona o'sishi</b>",
        "en": "📈 <b>Last 30 Days: Library Growth</b>",
        "ru": "📈 <b>Последние 30 дней: рост библиотеки</b>",
    },
    "admin.growth.entry": {
        "uz": "• <b>{day}</b> — {count} yangi versiya",
        "en": "• <b>{day}</b> — {count} new versions",
        "ru": "• <b>{day}</b> — {count} новых версий",
    },

    # ────────────────────────────────────────────────────────────────────────
    # ADMIN — broadcast
    # ────────────────────────────────────────────────────────────────────────
    "admin.broadcast.title": {
        "uz": "📢 <b>Xabar tarqatish</b>",
        "en": "📢 <b>Broadcast</b>",
        "ru": "📢 <b>Рассылка</b>",
    },
    "admin.broadcast.prompt": {
        "uz": "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabarni yuboring.",
        "en": "Send the message you want to broadcast to all users.",
        "ru": "Отправьте сообщение, которое хотите разослать всем пользователям.",
    },
    "admin.broadcast.text_only_note": {
        "uz": "<i>Faqat matn xabarlari qo'llab-quvvatlanadi (V1).</i>",
        "en": "<i>Only text messages are supported (V1).</i>",
        "ru": "<i>Поддерживаются только текстовые сообщения (V1).</i>",
    },
    "admin.broadcast.text_only_error": {
        "uz": "❗️ Faqat matn xabarlari qo'llab-quvvatlanadi.\nIltimos, matn ko'rinishida xabar yuboring.",
        "en": "❗️ Only text messages are supported.\nPlease send a text message.",
        "ru": "❗️ Поддерживаются только текстовые сообщения.\nПожалуйста, отправьте текст.",
    },
    "admin.broadcast.preview_header": {
        "uz": "👀 <b>Ko'rinish (Preview):</b>",
        "en": "👀 <b>Preview:</b>",
        "ru": "👀 <b>Предварительный просмотр:</b>",
    },
    "admin.broadcast.preview_note": {
        "uz": "📤 Barcha ro'yxatdan o'tgan foydalanuvchilarga yuboriladi.\nTasdiqlaysizmi?",
        "en": "📤 This will be sent to all registered users.\nDo you confirm?",
        "ru": "📤 Будет отправлено всем зарегистрированным пользователям.\nПодтверждаете?",
    },
    "admin.broadcast.no_text": {
        "uz": "⚠️ Xabar topilmadi. Iltimos, /admin orqali qayta urinib ko'ring.",
        "en": "⚠️ Message not found. Please try again via /admin.",
        "ru": "⚠️ Сообщение не найдено. Пожалуйста, попробуйте снова через /admin.",
    },
    "admin.broadcast.started_title": {
        "uz": "📢 <b>Broadcast boshlandi!</b>",
        "en": "📢 <b>Broadcast started!</b>",
        "ru": "📢 <b>Рассылка запущена!</b>",
    },
    "admin.broadcast.started_count": {
        "uz": "📊 Jami <b>{total}</b> ta foydalanuvchiga xabar yuborilmoqda.",
        "en": "📊 Sending to <b>{total}</b> users in total.",
        "ru": "📊 Отправляется <b>{total}</b> пользователям.",
    },
    "admin.broadcast.started_note": {
        "uz": "Jarayon tugagach statistika siz ga alohida xabar sifatida yuboriladi. ✅",
        "en": "The stats will be sent to you as a separate message when done. ✅",
        "ru": "По завершении статистика будет отправлена вам отдельным сообщением. ✅",
    },
    "admin.broadcast.answer_started": {
        "uz": "Broadcast boshlandi!",
        "en": "Broadcast started!",
        "ru": "Рассылка запущена!",
    },
    "admin.broadcast.cancelled": {
        "uz": "Bekor qilindi.",
        "en": "Cancelled.",
        "ru": "Отменено.",
    },
    "admin.broadcast.btn.send": {
        "uz": "✅ Yuborish",
        "en": "✅ Send",
        "ru": "✅ Отправить",
    },
    "admin.broadcast.btn.cancel": {
        "uz": "❌ Bekor qilish",
        "en": "❌ Cancel",
        "ru": "❌ Отменить",
    },
    "admin.broadcast.stats.title": {
        "uz": "📊 <b>Broadcast yakunlandi!</b>",
        "en": "📊 <b>Broadcast completed!</b>",
        "ru": "📊 <b>Рассылка завершена!</b>",
    },
    "admin.broadcast.stats.total": {
        "uz": "👥 Jami foydalanuvchilar: <b>{value}</b>",
        "en": "👥 Total users: <b>{value}</b>",
        "ru": "👥 Всего пользователей: <b>{value}</b>",
    },
    "admin.broadcast.stats.sent": {
        "uz": "✅ Muvaffaqiyatli yuborildi: <b>{value}</b>",
        "en": "✅ Successfully sent: <b>{value}</b>",
        "ru": "✅ Успешно отправлено: <b>{value}</b>",
    },
    "admin.broadcast.stats.failed": {
        "uz": "❌ Yuborilmadi (xato): <b>{value}</b>",
        "en": "❌ Failed (errors): <b>{value}</b>",
        "ru": "❌ Не отправлено (ошибки): <b>{value}</b>",
    },
    "admin.broadcast.stats.blocked": {
        "uz": "🚫 Bot bloklangan: <b>{value}</b>",
        "en": "🚫 Bot blocked: <b>{value}</b>",
        "ru": "🚫 Бот заблокирован: <b>{value}</b>",
    },
    "admin.broadcast.stats.elapsed": {
        "uz": "⏱ Umumiy vaqt: <b>{value}</b>",
        "en": "⏱ Total time: <b>{value}</b>",
        "ru": "⏱ Общее время: <b>{value}</b>",
    },

    # ────────────────────────────────────────────────────────────────────────
    # ADMIN — referral control panel (admin side)
    # ────────────────────────────────────────────────────────────────────────
    "admin.referral.title": {
        "uz": "👥 <b>Referral boshqaruvi</b>",
        "en": "👥 <b>Referral Management</b>",
        "ru": "👥 <b>Управление рефералами</b>",
    },
    "admin.referral.subtitle": {
        "uz": "Quyidagi bo'limlardan birini tanlang:",
        "en": "Choose one of the sections below:",
        "ru": "Выберите один из разделов ниже:",
    },
    "admin.referral.cancelled": {
        "uz": "Bekor qilindi.",
        "en": "Cancelled.",
        "ru": "Отменено.",
    },
    "admin.referral.user_not_found": {
        "uz": "❌ Foydalanuvchi topilmadi. Telegram ID yoki @username kiriting.",
        "en": "❌ User not found. Enter a Telegram ID or @username.",
        "ru": "❌ Пользователь не найден. Введите Telegram ID или @username.",
    },
    "admin.referral.id_not_found": {
        "uz": "❌ ID={telegram_id} bo'lgan foydalanuvchi topilmadi.",
        "en": "❌ User with ID={telegram_id} not found.",
        "ru": "❌ Пользователь с ID={telegram_id} не найден.",
    },
    "admin.referral.not_found_short": {
        "uz": "Foydalanuvchi topilmadi.",
        "en": "User not found.",
        "ru": "Пользователь не найден.",
    },
    "admin.referral.reset_done": {
        "uz": "✅ {amount} tanga reset qilindi.",
        "en": "✅ {amount} coins reset.",
        "ru": "✅ {amount} монет сброшено.",
    },
    "admin.referral.reset_answer": {
        "uz": "✅ {amount} tanga reset qilindi!",
        "en": "✅ {amount} coins reset!",
        "ru": "✅ {amount} монет сброшено!",
    },
    "admin.referral.coin_prompt": {
        "uz": "💬 Tanga miqdorini kiriting ({action} uchun):\n\n<i>Faqat musbat butun son kiriting, masalan: 50</i>",
        "en": "💬 Enter the coin amount (for {action}):\n\n<i>Enter a positive integer only, e.g. 50</i>",
        "ru": "💬 Введите количество монет (для {action}):\n\n<i>Введите только положительное целое число, например: 50</i>",
    },
    "admin.referral.invalid_amount": {
        "uz": "❌ Noto'g'ri miqdor. Musbat butun son kiriting:",
        "en": "❌ Invalid amount. Enter a positive integer:",
        "ru": "❌ Неверное количество. Введите положительное целое число:",
    },
    "admin.referral.coin_added": {
        "uz": "✅ {amount} 🪙 qo'shildi.",
        "en": "✅ {amount} 🪙 added.",
        "ru": "✅ {amount} 🪙 добавлено.",
    },
    "admin.referral.coin_removed": {
        "uz": "✅ {amount} 🪙 olindi.",
        "en": "✅ {amount} 🪙 removed.",
        "ru": "✅ {amount} 🪙 снято.",
    },
    "admin.referral.coin_insufficient": {
        "uz": "❌ Balansi yetarli emas.",
        "en": "❌ Insufficient balance.",
        "ru": "❌ Недостаточно средств.",
    },
    "admin.referral.bonus_given": {
        "uz": "✅ {amount} 🪙 bonus berildi.",
        "en": "✅ {amount} 🪙 bonus granted.",
        "ru": "✅ {amount} 🪙 бонус выдан.",
    },
    "admin.referral.unknown_action": {
        "uz": "❌ Noma'lum amal.",
        "en": "❌ Unknown action.",
        "ru": "❌ Неизвестное действие.",
    },
    "admin.referral.coin_history_header": {
        "uz": "📜 <b>Tanga tarixi</b>: {name}\nID: <code>{telegram_id}</code>",
        "en": "📜 <b>Coin History</b>: {name}\nID: <code>{telegram_id}</code>",
        "ru": "📜 <b>История монет</b>: {name}\nID: <code>{telegram_id}</code>",
    },
    "admin.referral.search.title": {
        "uz": "🔍 <b>Foydalanuvchi qidirish</b>",
        "en": "🔍 <b>Search User</b>",
        "ru": "🔍 <b>Поиск пользователя</b>",
    },
    "admin.referral.search.prompt": {
        "uz": "Telegram ID yoki @username kiriting:",
        "en": "Enter a Telegram ID or @username:",
        "ru": "Введите Telegram ID или @username:",
    },
    "admin.referral.search.hint": {
        "uz": "<i>Masalan: 123456789 yoki @username</i>",
        "en": "<i>Example: 123456789 or @username</i>",
        "ru": "<i>Пример: 123456789 или @username</i>",
    },
    "admin.referral.action.add": {
        "uz": "qo'shish",
        "en": "add",
        "ru": "добавить",
    },
    "admin.referral.action.remove": {
        "uz": "olish",
        "en": "remove",
        "ru": "снять",
    },
    "admin.referral.action.bonus": {
        "uz": "bonus berish",
        "en": "give bonus",
        "ru": "выдать бонус",
    },
    "admin.referral.tx.add_reason": {
        "uz": "Admin qo'lda qo'shdi",
        "en": "Admin manual add",
        "ru": "Добавлено администратором",
    },
    "admin.referral.tx.remove_reason": {
        "uz": "Admin qo'lda oldi",
        "en": "Admin manual remove",
        "ru": "Снято администратором",
    },
    "admin.referral.tx.bonus_reason": {
        "uz": "Admin bonusi",
        "en": "Admin bonus",
        "ru": "Бонус от администратора",
    },

    # ────────────────────────────────────────────────────────────────────────
    # ADMIN — referral keyboard buttons
    # ────────────────────────────────────────────────────────────────────────
    "admin.referral.btn.top_referrers": {
        "uz": "🏆 Top referralchilar",
        "en": "🏆 Top Referrers",
        "ru": "🏆 Топ рефереров",
    },
    "admin.referral.btn.top_holders": {
        "uz": "🪙 Top tanga egalari",
        "en": "🪙 Top Coin Holders",
        "ru": "🪙 Топ владельцев монет",
    },
    "admin.referral.btn.recent": {
        "uz": "🕐 So'nggi referrallar",
        "en": "🕐 Recent Referrals",
        "ru": "🕐 Последние рефералы",
    },
    "admin.referral.btn.search": {
        "uz": "🔍 Foydalanuvchi qidirish",
        "en": "🔍 Search User",
        "ru": "🔍 Поиск пользователя",
    },
    "admin.referral.btn.stats": {
        "uz": "📊 Referral statistikasi",
        "en": "📊 Referral Statistics",
        "ru": "📊 Статистика рефералов",
    },
    "admin.referral.btn.back": {
        "uz": "⬅️ Referral boshqaruvi",
        "en": "⬅️ Referral Management",
        "ru": "⬅️ Управление рефералами",
    },
    "admin.referral.btn.home": {
        "uz": "🏠 Admin menyu",
        "en": "🏠 Admin Menu",
        "ru": "🏠 Меню администратора",
    },
    "admin.referral.btn.add_coins": {
        "uz": "➕ Tanga qo'shish",
        "en": "➕ Add Coins",
        "ru": "➕ Добавить монеты",
    },
    "admin.referral.btn.remove_coins": {
        "uz": "➖ Tanga olish",
        "en": "➖ Remove Coins",
        "ru": "➖ Снять монеты",
    },
    "admin.referral.btn.reset_coins": {
        "uz": "🔄 Tangani reset",
        "en": "🔄 Reset Coins",
        "ru": "🔄 Сбросить монеты",
    },
    "admin.referral.btn.bonus": {
        "uz": "🎁 Bonus berish",
        "en": "🎁 Give Bonus",
        "ru": "🎁 Выдать бонус",
    },
    "admin.referral.btn.history": {
        "uz": "📜 Tarix ko'rish",
        "en": "📜 View History",
        "ru": "📜 История",
    },
    "admin.referral.btn.cancel_action": {
        "uz": "❌ Bekor qilish",
        "en": "❌ Cancel",
        "ru": "❌ Отменить",
    },

    # ────────────────────────────────────────────────────────────────────────
    # ADMIN — referral formatter strings
    # ────────────────────────────────────────────────────────────────────────
    "admin.referral.top_referrers.title": {
        "uz": "🏆 <b>Top referralchilar</b>",
        "en": "🏆 <b>Top Referrers</b>",
        "ru": "🏆 <b>Топ рефереров</b>",
    },
    "admin.referral.top_referrers.empty": {
        "uz": "Hali referral yo'q.",
        "en": "No referrals yet.",
        "ru": "Рефералов пока нет.",
    },
    "admin.referral.top_referrers.invites": {
        "uz": "ta taklif",
        "en": "referrals",
        "ru": "реферала(ов)",
    },
    "admin.referral.top_referrers.earned": {
        "uz": "Topgan",
        "en": "Earned",
        "ru": "Заработано",
    },
    "admin.referral.top_referrers.balance": {
        "uz": "Balans",
        "en": "Balance",
        "ru": "Баланс",
    },
    "admin.referral.top_holders.title": {
        "uz": "🪙 <b>Top tanga egalari</b>",
        "en": "🪙 <b>Top Coin Holders</b>",
        "ru": "🪙 <b>Топ владельцев монет</b>",
    },
    "admin.referral.top_holders.empty": {
        "uz": "Hali tanga yo'q.",
        "en": "No coins yet.",
        "ru": "Монет пока нет.",
    },
    "admin.referral.top_holders.invites": {
        "uz": "Taklif",
        "en": "Referrals",
        "ru": "Рефералы",
    },
    "admin.referral.recent.title": {
        "uz": "🕐 <b>So'nggi referrallar</b>",
        "en": "🕐 <b>Recent Referrals</b>",
        "ru": "🕐 <b>Последние рефералы</b>",
    },
    "admin.referral.recent.empty": {
        "uz": "Hali referral yo'q.",
        "en": "No referrals yet.",
        "ru": "Рефералов пока нет.",
    },
    "admin.referral.stats.title": {
        "uz": "📊 <b>Referral statistikasi</b>",
        "en": "📊 <b>Referral Statistics</b>",
        "ru": "📊 <b>Статистика рефералов</b>",
    },
    "admin.referral.stats.total": {
        "uz": "👥 Jami muvaffaqiyatli referrallar: <b>{value}</b>",
        "en": "👥 Total successful referrals: <b>{value}</b>",
        "ru": "👥 Всего успешных рефералов: <b>{value}</b>",
    },
    "admin.referral.stats.unique": {
        "uz": "🙋 Nechta foydalanuvchi taklif qildi: <b>{value}</b>",
        "en": "🙋 Users who referred others: <b>{value}</b>",
        "ru": "🙋 Пользователей, пригласивших других: <b>{value}</b>",
    },
    "admin.referral.stats.total_coins": {
        "uz": "💰 Jami tanga mukofoti berildi: <b>{value} 🪙</b>",
        "en": "💰 Total coin rewards given: <b>{value} 🪙</b>",
        "ru": "💰 Всего выдано монет в награду: <b>{value} 🪙</b>",
    },
    "admin.referral.stats.circulation": {
        "uz": "🏦 Aylanmadagi tangalar: <b>{value} 🪙</b>",
        "en": "🏦 Coins in circulation: <b>{value} 🪙</b>",
        "ru": "🏦 Монет в обороте: <b>{value} 🪙</b>",
    },
    "admin.referral.stats.ever_earned": {
        "uz": "📈 Jami topilgan tangalar: <b>{value} 🪙</b>",
        "en": "📈 Total coins ever earned: <b>{value} 🪙</b>",
        "ru": "📈 Всего заработано монет: <b>{value} 🪙</b>",
    },
    "admin.referral.profile.reg_date": {
        "uz": "📅 Ro'yxatdan: {date}",
        "en": "📅 Registered: {date}",
        "ru": "📅 Зарегистрирован: {date}",
    },
    "admin.referral.profile.premium_yes": {
        "uz": "💎 Ha",
        "en": "💎 Yes",
        "ru": "💎 Да",
    },
    "admin.referral.profile.premium_no": {
        "uz": "❌ Yo'q",
        "en": "❌ No",
        "ru": "❌ Нет",
    },
    "admin.referral.profile.premium_label": {
        "uz": "💎 Premium: {value}",
        "en": "💎 Premium: {value}",
        "ru": "💎 Premium: {value}",
    },
    "admin.referral.profile.coin_balance": {
        "uz": "🪙 Tanga balansi: <b>{value}</b>",
        "en": "🪙 Coin balance: <b>{value}</b>",
        "ru": "🪙 Баланс монет: <b>{value}</b>",
    },
    "admin.referral.profile.lifetime_earned": {
        "uz": "📈 Jami topilgan: {value}",
        "en": "📈 Lifetime earned: {value}",
        "ru": "📈 Всего заработано: {value}",
    },
    "admin.referral.profile.lifetime_spent": {
        "uz": "📉 Jami sarflangan: {value}",
        "en": "📉 Lifetime spent: {value}",
        "ru": "📉 Всего потрачено: {value}",
    },
    "admin.referral.profile.invites": {
        "uz": "👥 Taklif etilgan do'stlar: <b>{value}</b>",
        "en": "👥 Friends invited: <b>{value}</b>",
        "ru": "👥 Приглашённых друзей: <b>{value}</b>",
    },
    "admin.referral.profile.referrer": {
        "uz": "🔗 Taklif qiluvchi: {value}",
        "en": "🔗 Referred by: {value}",
        "ru": "🔗 Кто пригласил: {value}",
    },
    "admin.referral.profile.no_referrer": {
        "uz": "Yo'q",
        "en": "None",
        "ru": "Нет",
    },
    "admin.referral.profile.referral_code": {
        "uz": "🎫 Referral kodi: <code>{value}</code>",
        "en": "🎫 Referral code: <code>{value}</code>",
        "ru": "🎫 Реферальный код: <code>{value}</code>",
    },
    "admin.referral.profile.recent_tx_title": {
        "uz": "📋 <b>So'nggi 5 ta operatsiya:</b>",
        "en": "📋 <b>Last 5 transactions:</b>",
        "ru": "📋 <b>Последние 5 операций:</b>",
    },

    # ────────────────────────────────────────────────────────────────────────
    # REFERRAL — user-facing invite page
    # ────────────────────────────────────────────────────────────────────────
    "referral.invite.title": {
        "uz": "👥 <b>Do'stlarni taklif qiling</b>",
        "en": "👥 <b>Invite Friends</b>",
        "ru": "👥 <b>Пригласите друзей</b>",
    },
    "referral.invite.tagline": {
        "uz": "Do'stlaringizni taklif eting va tanga yuting!",
        "en": "Invite your friends and earn coins!",
        "ru": "Приглашайте друзей и зарабатывайте монеты!",
    },
    "referral.invite.balance": {
        "uz": "💰 Joriy balans:  <b>🪙 {balance} tanga</b>",
        "en": "💰 Current balance:  <b>🪙 {balance} coins</b>",
        "ru": "💰 Текущий баланс:  <b>🪙 {balance} монет</b>",
    },
    "referral.invite.count": {
        "uz": "✅ Muvaffaqiyatli taklif:  <b>{count} ta</b>",
        "en": "✅ Successful referrals:  <b>{count}</b>",
        "ru": "✅ Успешных приглашений:  <b>{count}</b>",
    },
    "referral.invite.next_reward": {
        "uz": "🎁 Keyingi taklif mukofoti:  <b>🪙 {reward} tanga</b>",
        "en": "🎁 Next referral reward:  <b>🪙 {reward} coins</b>",
        "ru": "🎁 Следующая награда за реферала:  <b>🪙 {reward} монет</b>",
    },
    "referral.invite.link": {
        "uz": "🔗 Sizning taklif havolangiz:",
        "en": "🔗 Your invite link:",
        "ru": "🔗 Ваша реферальная ссылка:",
    },
    "referral.milestone.congrats": {
        "uz": "🎯 <b>Tabriklaymiz!</b>",
        "en": "🎯 <b>Congratulations!</b>",
        "ru": "🎯 <b>Поздравляем!</b>",
    },
    "referral.milestone.can_afford": {
        "uz": "✅ Sizda {cost} tangadan ortiq bor.\nPremium faollashtirish tez orada ishga tushadi! 🚀",
        "en": "✅ You have more than {cost} coins.\nPremium activation is coming soon! 🚀",
        "ru": "✅ У вас больше {cost} монет.\nАктивация Premium скоро появится! 🚀",
    },
    "referral.milestone.goal_title": {
        "uz": "🎯 <b>Keyingi maqsad</b>",
        "en": "🎯 <b>Next Goal</b>",
        "ru": "🎯 <b>Следующая цель</b>",
    },
    "referral.milestone.friends_one": {
        "uz": "👉 1 ta do'st taklif qiling",
        "en": "👉 Invite 1 friend",
        "ru": "👉 Пригласите 1 друга",
    },
    "referral.milestone.friends_many": {
        "uz": "👉 {n} ta do'st taklif qiling",
        "en": "👉 Invite {n} friends",
        "ru": "👉 Пригласите {n} друзей",
    },
    "referral.milestone.coins_needed": {
        "uz": "💰 Yana {coins} tanga kerak (1 kun Premium = {cost} tanga)",
        "en": "💰 You need {coins} more coins (1 day Premium = {cost} coins)",
        "ru": "💰 Нужно ещё {coins} монет (1 день Premium = {cost} монет)",
    },
    "referral.milestone.referral_earn": {
        "uz": "📈 {n} ta taklif = +{coins} tanga",
        "en": "📈 {n} referrals = +{coins} coins",
        "ru": "📈 {n} реферала(ов) = +{coins} монет",
    },
    "referral.milestone.cta": {
        "uz": "Do'stlaringizni taklif qiling va Premium yuting! 🚀",
        "en": "Invite your friends and win Premium! 🚀",
        "ru": "Приглашайте друзей и выиграйте Premium! 🚀",
    },
    "referral.not_registered": {
        "uz": "Iltimos, avval ro'yxatdan o'ting.",
        "en": "Please register first.",
        "ru": "Пожалуйста, сначала зарегистрируйтесь.",
    },
    "referral.refreshed": {
        "uz": "♻️ Yangilandi!",
        "en": "♻️ Refreshed!",
        "ru": "♻️ Обновлено!",
    },

    # ────────────────────────────────────────────────────────────────────────
    # REFERRAL — user keyboard buttons
    # ────────────────────────────────────────────────────────────────────────
    "referral.btn.coin_history": {
        "uz": "🪙 Tanga tarixim",
        "en": "🪙 Coin History",
        "ru": "🪙 История монет",
    },
    "referral.btn.refresh": {
        "uz": "🔄 Yangilash",
        "en": "🔄 Refresh",
        "ru": "🔄 Обновить",
    },
    "referral.btn.home": {
        "uz": "🏠 Bosh sahifa",
        "en": "🏠 Home",
        "ru": "🏠 Главная",
    },
    "referral.btn.back_to_invite": {
        "uz": "⬅️ Do'stlarni taklif qilish",
        "en": "⬅️ Invite Friends",
        "ru": "⬅️ Пригласить друзей",
    },

    # ────────────────────────────────────────────────────────────────────────
    # COINS — history page
    # ────────────────────────────────────────────────────────────────────────
    "coins.history.title": {
        "uz": "🪙 <b>Tanga tarixi</b>",
        "en": "🪙 <b>Coin History</b>",
        "ru": "🪙 <b>История монет</b>",
    },
    "coins.history.balance": {
        "uz": "💰 Joriy balans:       <b>{balance} 🪙</b>",
        "en": "💰 Current balance:    <b>{balance} 🪙</b>",
        "ru": "💰 Текущий баланс:     <b>{balance} 🪙</b>",
    },
    "coins.history.earned": {
        "uz": "📈 Jami topilgan:      <b>+{earned} 🪙</b>",
        "en": "📈 Total earned:       <b>+{earned} 🪙</b>",
        "ru": "📈 Всего заработано:   <b>+{earned} 🪙</b>",
    },
    "coins.history.spent": {
        "uz": "📉 Jami sarflangan:    <b>-{spent} 🪙</b>",
        "en": "📉 Total spent:        <b>-{spent} 🪙</b>",
        "ru": "📉 Всего потрачено:    <b>-{spent} 🪙</b>",
    },
    "coins.history.recent": {
        "uz": "📋 <b>So'nggi operatsiyalar:</b>",
        "en": "📋 <b>Recent transactions:</b>",
        "ru": "📋 <b>Последние операции:</b>",
    },
    "coins.history.empty": {
        "uz": "Hali hech qanday operatsiya yo'q.",
        "en": "No transactions yet.",
        "ru": "Операций пока нет.",
    },
    "coins.tx.referral": {
        "uz": "Referral",
        "en": "Referral",
        "ru": "Реферал",
    },
    "coins.tx.welcome_bonus": {
        "uz": "Xush kelibsiz bonusi",
        "en": "Welcome bonus",
        "ru": "Приветственный бонус",
    },
    "coins.tx.admin_add": {
        "uz": "Admin qo'shdi",
        "en": "Admin added",
        "ru": "Добавлено администратором",
    },
    "coins.tx.admin_remove": {
        "uz": "Admin oldi",
        "en": "Admin removed",
        "ru": "Снято администратором",
    },
    "coins.tx.admin_reset": {
        "uz": "Admin reset",
        "en": "Admin reset",
        "ru": "Сброс администратором",
    },
    "coins.tx.bonus": {
        "uz": "Bonus",
        "en": "Bonus",
        "ru": "Бонус",
    },
    "coins.tx.premium_redeem": {
        "uz": "Premium",
        "en": "Premium",
        "ru": "Premium",
    },

    # ────────────────────────────────────────────────────────────────────────
    # GATEWAY — admin control panel
    # ────────────────────────────────────────────────────────────────────────
    "gateway.not_active": {
        "uz": "ℹ️ AI Gateway faol emas. AI_PROVIDER=gateway sozlamasini .env ga qo'shing.",
        "en": "ℹ️ AI Gateway is not active. Set AI_PROVIDER=gateway in your .env file.",
        "ru": "ℹ️ AI Gateway не активен. Установите AI_PROVIDER=gateway в файле .env.",
    },
    "gateway.status.title": {
        "uz": "🤖 <b>AI Gateway — Asosiy holat</b>",
        "en": "🤖 <b>AI Gateway — Overview</b>",
        "ru": "🤖 <b>AI Gateway — Обзор</b>",
    },
    "gateway.status.maintenance_on": {
        "uz": "🔒 TEXNIK ISHLAR REJIMI",
        "en": "🔒 MAINTENANCE MODE",
        "ru": "🔒 РЕЖИМ ОБСЛУЖИВАНИЯ",
    },
    "gateway.status.online": {
        "uz": "🟢 Faol",
        "en": "🟢 Online",
        "ru": "🟢 Активен",
    },
    "gateway.status.analytics": {
        "uz": "📊 <b>Umumiy statistika</b>",
        "en": "📊 <b>Overall Statistics</b>",
        "ru": "📊 <b>Общая статистика</b>",
    },
    "gateway.status.total_requests": {
        "uz": "  Jami so'rovlar: <b>{value}</b>",
        "en": "  Total requests: <b>{value}</b>",
        "ru": "  Всего запросов: <b>{value}</b>",
    },
    "gateway.status.errors": {
        "uz": "  Xatolar: <b>{value}</b>",
        "en": "  Errors: <b>{value}</b>",
        "ru": "  Ошибки: <b>{value}</b>",
    },
    "gateway.status.quota_failures": {
        "uz": "  Kvota xatolari: <b>{value}</b>",
        "en": "  Quota failures: <b>{value}</b>",
        "ru": "  Превышений квоты: <b>{value}</b>",
    },
    "gateway.status.fallbacks": {
        "uz": "  Fallback ishladi: <b>{value}</b>",
        "en": "  Fallbacks triggered: <b>{value}</b>",
        "ru": "  Сработавших fallback: <b>{value}</b>",
    },
    "gateway.status.free_requests": {
        "uz": "  Bepul foydalanuvchilar: <b>{value}</b>",
        "en": "  Free user requests: <b>{value}</b>",
        "ru": "  Запросы бесплатных: <b>{value}</b>",
    },
    "gateway.status.premium_requests": {
        "uz": "  Premium foydalanuvchilar: <b>{value}</b>",
        "en": "  Premium user requests: <b>{value}</b>",
        "ru": "  Запросы Premium: <b>{value}</b>",
    },
    "gateway.status.healthy_keys": {
        "uz": "🔑 Sog'lom kalitlar: <b>{healthy}/{total}</b>",
        "en": "🔑 Healthy keys: <b>{healthy}/{total}</b>",
        "ru": "🔑 Здоровых ключей: <b>{healthy}/{total}</b>",
    },
    "gateway.status.providers_title": {
        "uz": "🏭 <b>Provayderlar holati</b>",
        "en": "🏭 <b>Provider Status</b>",
        "ru": "🏭 <b>Статус провайдеров</b>",
    },
    "gateway.status.provider_entry": {
        "uz": "  {status} <b>{provider}</b> ({tier}) — {healthy}/{total} kalit, ~{latency}ms",
        "en": "  {status} <b>{provider}</b> ({tier}) — {healthy}/{total} keys, ~{latency}ms",
        "ru": "  {status} <b>{provider}</b> ({tier}) — {healthy}/{total} ключей, ~{latency}мс",
    },
    "gateway.key.title": {
        "uz": "🔑 <b>{label}</b>",
        "en": "🔑 <b>{label}</b>",
        "ru": "🔑 <b>{label}</b>",
    },
    "gateway.key.status.healthy": {
        "uz": "🟢 Sog'lom",
        "en": "🟢 Healthy",
        "ru": "🟢 Работает",
    },
    "gateway.key.status.paused": {
        "uz": "⏸ To'xtatilgan",
        "en": "⏸ Paused",
        "ru": "⏸ На паузе",
    },
    "gateway.key.status.down": {
        "uz": "🔴 Nofaol",
        "en": "🔴 Down",
        "ru": "🔴 Отключён",
    },
    "gateway.key.status.label": {
        "uz": "Holat: {value}",
        "en": "Status: {value}",
        "ru": "Статус: {value}",
    },
    "gateway.key.enabled_label": {
        "uz": "Yoqilgan: {value}",
        "en": "Enabled: {value}",
        "ru": "Включён: {value}",
    },
    "gateway.key.paused_label": {
        "uz": "To'xtatilgan: {value}",
        "en": "Paused: {value}",
        "ru": "На паузе: {value}",
    },
    "gateway.key.stats.title": {
        "uz": "📊 <b>Statistika</b>",
        "en": "📊 <b>Statistics</b>",
        "ru": "📊 <b>Статистика</b>",
    },
    "gateway.key.stats.total": {
        "uz": "  Jami so'rovlar: <b>{value}</b>",
        "en": "  Total requests: <b>{value}</b>",
        "ru": "  Всего запросов: <b>{value}</b>",
    },
    "gateway.key.stats.success": {
        "uz": "  Muvaffaqiyatli: <b>{value}</b>",
        "en": "  Successful: <b>{value}</b>",
        "ru": "  Успешных: <b>{value}</b>",
    },
    "gateway.key.stats.errors": {
        "uz": "  Xatolar: <b>{value}</b>",
        "en": "  Errors: <b>{value}</b>",
        "ru": "  Ошибок: <b>{value}</b>",
    },
    "gateway.key.stats.consecutive": {
        "uz": "  Ketma-ket xatolar: <b>{value}</b>",
        "en": "  Consecutive failures: <b>{value}</b>",
        "ru": "  Последовательных ошибок: <b>{value}</b>",
    },
    "gateway.key.stats.latency": {
        "uz": "  O'rtacha kechikish: <b>{value}ms</b>",
        "en": "  Average latency: <b>{value}ms</b>",
        "ru": "  Среднее время отклика: <b>{value}мс</b>",
    },
    "gateway.key.times.title": {
        "uz": "⏱ <b>Vaqtlar</b>",
        "en": "⏱ <b>Timestamps</b>",
        "ru": "⏱ <b>Временны́е метки</b>",
    },
    "gateway.key.times.last_success": {
        "uz": "  Oxirgi muvaffaqiyat: {value}",
        "en": "  Last success: {value}",
        "ru": "  Последний успех: {value}",
    },
    "gateway.key.times.last_failure": {
        "uz": "  Oxirgi xato: {value}",
        "en": "  Last failure: {value}",
        "ru": "  Последняя ошибка: {value}",
    },
    "gateway.key.times.cooldown": {
        "uz": "  Cooldown tugaydi: {value}",
        "en": "  Cooldown until: {value}",
        "ru": "  Кулдаун до: {value}",
    },
    "gateway.key.times.no_cooldown": {
        "uz": "Yo'q",
        "en": "None",
        "ru": "Нет",
    },
    "gateway.key.not_found": {
        "uz": "Kalit topilmadi",
        "en": "Key not found",
        "ru": "Ключ не найден",
    },
    "gateway.action.enabled": {
        "uz": "✅ {label} yoqildi",
        "en": "✅ {label} enabled",
        "ru": "✅ {label} включён",
    },
    "gateway.action.disabled": {
        "uz": "🔴 {label} o'chirildi",
        "en": "🔴 {label} disabled",
        "ru": "🔴 {label} отключён",
    },
    "gateway.action.paused": {
        "uz": "⏸ {label} to'xtatildi",
        "en": "⏸ {label} paused",
        "ru": "⏸ {label} приостановлен",
    },
    "gateway.action.resumed": {
        "uz": "▶️ {label} davom ettirildi",
        "en": "▶️ {label} resumed",
        "ru": "▶️ {label} возобновлён",
    },
    "gateway.action.key_not_found": {
        "uz": "❌ Kalit topilmadi",
        "en": "❌ Key not found",
        "ru": "❌ Ключ не найден",
    },
    "gateway.test.loading": {
        "uz": "⏳ Sinov so'rovi yuborilmoqda…",
        "en": "⏳ Sending test request…",
        "ru": "⏳ Отправляю тестовый запрос…",
    },
    "gateway.test.result": {
        "uz": "🧪 <b>Kalit sinov natijasi:</b>",
        "en": "🧪 <b>Key test result:</b>",
        "ru": "🧪 <b>Результат теста ключа:</b>",
    },
    "gateway.provider.title": {
        "uz": "🏭 <b>{provider} provayder boshqaruvi</b>",
        "en": "🏭 <b>{provider} Provider Control</b>",
        "ru": "🏭 <b>Управление провайдером {provider}</b>",
    },
    "gateway.provider.no_keys": {
        "uz": "  Hech qanday kalit ro'yxatdan o'tmagan.",
        "en": "  No keys registered.",
        "ru": "  Ключи не зарегистрированы.",
    },
    "gateway.provider.enabled": {
        "uz": "✅ {provider} yoqildi",
        "en": "✅ {provider} enabled",
        "ru": "✅ {provider} включён",
    },
    "gateway.provider.disabled": {
        "uz": "🔴 {provider} o'chirildi",
        "en": "🔴 {provider} disabled",
        "ru": "🔴 {provider} отключён",
    },
    "gateway.keys.title": {
        "uz": "🔑 <b>{provider_label} kalitlar holati</b>",
        "en": "🔑 <b>{provider_label} Key Health</b>",
        "ru": "🔑 <b>Состояние ключей {provider_label}</b>",
    },
    "gateway.keys.all": {
        "uz": "Barcha",
        "en": "All",
        "ru": "Все",
    },
    "gateway.keys.empty": {
        "uz": "ℹ️ Hech qanday kalit ro'yxatdan o'tmagan.",
        "en": "ℹ️ No keys are registered.",
        "ru": "ℹ️ Ключи не зарегистрированы.",
    },
    "gateway.keys.entry": {
        "uz": "{status} {label} — {requests} so'rov",
        "en": "{status} {label} — {requests} requests",
        "ru": "{status} {label} — {requests} запросов",
    },
    "gateway.maintenance.on": {
        "uz": "🔒 Texnik ishlar rejimi yoqildi",
        "en": "🔒 Maintenance mode enabled",
        "ru": "🔒 Режим обслуживания включён",
    },
    "gateway.maintenance.off": {
        "uz": "🔓 Texnik ishlar rejimi o'chirildi",
        "en": "🔓 Maintenance mode disabled",
        "ru": "🔓 Режим обслуживания отключён",
    },
    "gateway.priority.gemini_first": {
        "uz": "✅ Ustuvorlik: Gemini → Groq",
        "en": "✅ Priority: Gemini → Groq",
        "ru": "✅ Приоритет: Gemini → Groq",
    },
    "gateway.priority.groq_first": {
        "uz": "✅ Ustuvorlik: Groq → Gemini",
        "en": "✅ Priority: Groq → Gemini",
        "ru": "✅ Приоритет: Groq → Gemini",
    },

    # ────────────────────────────────────────────────────────────────────────
    # GATEWAY — keyboard buttons
    # ────────────────────────────────────────────────────────────────────────
    "gateway.btn.status": {
        "uz": "📊 Gateway holati",
        "en": "📊 Gateway Status",
        "ru": "📊 Статус Gateway",
    },
    "gateway.btn.keys": {
        "uz": "🔑 Kalitlar holati",
        "en": "🔑 Key Health",
        "ru": "🔑 Состояние ключей",
    },
    "gateway.btn.gemini": {
        "uz": "🟢 Gemini boshqaruvi",
        "en": "🟢 Gemini Control",
        "ru": "🟢 Управление Gemini",
    },
    "gateway.btn.groq": {
        "uz": "⚡ Groq boshqaruvi",
        "en": "⚡ Groq Control",
        "ru": "⚡ Управление Groq",
    },
    "gateway.btn.maintenance_on": {
        "uz": "🔒 Texnik ishlar rejimi",
        "en": "🔒 Enable Maintenance",
        "ru": "🔒 Включить обслуживание",
    },
    "gateway.btn.maintenance_off": {
        "uz": "🔓 Texnik ishlarni tugatish",
        "en": "🔓 Disable Maintenance",
        "ru": "🔓 Выключить обслуживание",
    },
    "gateway.btn.priority_gemini": {
        "uz": "🔀 Ustuvorlik: Gemini → Groq",
        "en": "🔀 Priority: Gemini → Groq",
        "ru": "🔀 Приоритет: Gemini → Groq",
    },
    "gateway.btn.priority_groq": {
        "uz": "🔀 Ustuvorlik: Groq → Gemini",
        "en": "🔀 Priority: Groq → Gemini",
        "ru": "🔀 Приоритет: Groq → Gemini",
    },
    "gateway.btn.back": {
        "uz": "⬅️ Admin menyu",
        "en": "⬅️ Admin Menu",
        "ru": "⬅️ Меню администратора",
    },
    "gateway.btn.provider_disable": {
        "uz": "🔴 {provider} o'chirish",
        "en": "🔴 Disable {provider}",
        "ru": "🔴 Отключить {provider}",
    },
    "gateway.btn.provider_enable": {
        "uz": "🟢 {provider} yoqish",
        "en": "🟢 Enable {provider}",
        "ru": "🟢 Включить {provider}",
    },
    "gateway.btn.provider_keys": {
        "uz": "🔑 {provider} kalitlari",
        "en": "🔑 {provider} Keys",
        "ru": "🔑 Ключи {provider}",
    },
    "gateway.btn.provider_back": {
        "uz": "⬅️ Gateway bosh menyusi",
        "en": "⬅️ Gateway Main Menu",
        "ru": "⬅️ Главное меню Gateway",
    },
    "gateway.btn.key_enable": {
        "uz": "🟢 Kalitni yoqish",
        "en": "🟢 Enable Key",
        "ru": "🟢 Включить ключ",
    },
    "gateway.btn.key_disable": {
        "uz": "🔴 Kalitni o'chirish",
        "en": "🔴 Disable Key",
        "ru": "🔴 Отключить ключ",
    },
    "gateway.btn.key_pause": {
        "uz": "⏸ Kalitni vaqtincha to'xtatish",
        "en": "⏸ Pause Key",
        "ru": "⏸ Приостановить ключ",
    },
    "gateway.btn.key_resume": {
        "uz": "▶️ Kalitni davom ettirish",
        "en": "▶️ Resume Key",
        "ru": "▶️ Возобновить ключ",
    },
    "gateway.btn.key_test": {
        "uz": "🧪 Kalitni sinab ko'rish",
        "en": "🧪 Test Key",
        "ru": "🧪 Протестировать ключ",
    },
    "gateway.btn.keys_back": {
        "uz": "⬅️ Kalitlar ro'yxati",
        "en": "⬅️ Key List",
        "ru": "⬅️ Список ключей",
    },
    # ──────────────────────────────────────────────────────────────────────────
    # VOCABULARY (V1.6) — My Vocabulary
    # ──────────────────────────────────────────────────────────────────────────
    "btn_my_vocabulary": {
        "uz": "\U0001f4da Mening lug'atim",
        "en": "\U0001f4da My Vocabulary",
        "ru": "\U0001f4da \u041c\u043e\u0439 \u0441\u043b\u043e\u0432\u0430\u0440\u044c",
    },
    "vocab.title": {
        "uz": "\U0001f4da <b>Mening lug'atim</b> ({total} ta so'z)",
        "en": "\U0001f4da <b>My Vocabulary</b> ({total} words)",
        "ru": "\U0001f4da <b>\u041c\u043e\u0439 \u0441\u043b\u043e\u0432\u0430\u0440\u044c</b> ({total} \u0441\u043b\u043e\u0432)",
    },
    "vocab.empty": {
        "uz": (
            "\U0001f4da <b>Mening lug'atim</b>\n\n"
            "Hali hech qanday so'z yo'q.\n\n"
            "MneVoca orqali birinchi so'zingizni qo'shing!"
        ),
        "en": (
            "\U0001f4da <b>My Vocabulary</b>\n\n"
            "No words yet.\n\n"
            "Use MneVoca to add your first word!"
        ),
        "ru": (
            "\U0001f4da <b>\u041c\u043e\u0439 \u0441\u043b\u043e\u0432\u0430\u0440\u044c</b>\n\n"
            "\u0421\u043b\u043e\u0432 \u043f\u043e\u043a\u0430 \u043d\u0435\u0442.\n\n"
            "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 MneVoca, \u0447\u0442\u043e\u0431\u044b \u0434\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043f\u0435\u0440\u0432\u043e\u0435 \u0441\u043b\u043e\u0432\u043e!"
        ),
    },
    "vocab.page_indicator": {
        "uz": "{current}/{total}",
        "en": "{current}/{total}",
        "ru": "{current}/{total}",
    },
    "vocab.search_prompt": {
        "uz": "\U0001f50d So'z yoki ma'nosini kiriting:",
        "en": "\U0001f50d Enter a word or its meaning:",
        "ru": "\U0001f50d \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u043b\u043e\u0432\u043e \u0438\u043b\u0438 \u0435\u0433\u043e \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435:",
    },
    "vocab.search_no_results": {
        "uz": "\U0001f50d <b>{query}</b> bo'yicha hech narsa topilmadi.",
        "en": "\U0001f50d Nothing found for <b>{query}</b>.",
        "ru": "\U0001f50d \u041d\u0438\u0447\u0435\u0433\u043e \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e \u043f\u043e \u0437\u0430\u043f\u0440\u043e\u0441\u0443 <b>{query}</b>.",
    },
    "vocab.search_results_header": {
        "uz": "\U0001f50d <b>{query}</b> bo'yicha natijalar: {total} ta",
        "en": "\U0001f50d Results for <b>{query}</b>: {total}",
        "ru": "\U0001f50d \u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u044b \u043f\u043e <b>{query}</b>: {total}",
    },
    "vocab.entry_not_found": {
        "uz": "So'z topilmadi. Ehtimol u o'chirilgan.",
        "en": "Word not found. It may have been deleted.",
        "ru": "\u0421\u043b\u043e\u0432\u043e \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e. \u0412\u043e\u0437\u043c\u043e\u0436\u043d\u043e, \u043e\u043d\u043e \u0431\u044b\u043b\u043e \u0443\u0434\u0430\u043b\u0435\u043d\u043e.",
    },
    "vocab.label_favorited": {
        "uz": "\u2b50 Sevimlilar ro'yxatida",
        "en": "\u2b50 In your favorites",
        "ru": "\u2b50 \u0412 \u0438\u0437\u0431\u0440\u0430\u043d\u043d\u044b\u0445",
    },
    "vocab.label_update_available": {
        "uz": "\u2728 Yangi versiya mavjud! Pastdagi tugmani bosing.",
        "en": "\u2728 New mnemonic available! Tap the button below.",
        "ru": "\u2728 \u0414\u043e\u0441\u0442\u0443\u043f\u043d\u0430 \u043d\u043e\u0432\u0430\u044f \u043c\u043d\u0435\u043c\u043e\u043d\u0438\u043a\u0430! \u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443 \u043d\u0438\u0436\u0435.",
    },
    "vocab.delete_confirm_prompt": {
        "uz": "\U0001f5d1 <b>{word}</b> so'zini lug'atdan o'chirishni xohlaysizmi?\n\n<i>Bu faqat sizning nusxangizni o'chiradi.</i>",
        "en": "\U0001f5d1 Delete <b>{word}</b> from your vocabulary?\n\n<i>This only removes your personal copy.</i>",
        "ru": "\U0001f5d1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c <b>{word}</b> \u0438\u0437 \u0432\u0430\u0448\u0435\u0433\u043e \u0441\u043b\u043e\u0432\u0430\u0440\u044f?\n\n<i>\u0423\u0434\u0430\u043b\u044f\u0435\u0442\u0441\u044f \u0442\u043e\u043b\u044c\u043a\u043e \u0432\u0430\u0448\u0430 \u043b\u0438\u0447\u043d\u0430\u044f \u043a\u043e\u043f\u0438\u044f.</i>",
    },
    "vocab.update.title": {
        "uz": "\u2728 Yangi mnemonika mavjud",
        "en": "\u2728 New Mnemonic Available",
        "ru": "\u2728 \u0414\u043e\u0441\u0442\u0443\u043f\u043d\u0430 \u043d\u043e\u0432\u0430\u044f \u043c\u043d\u0435\u043c\u043e\u043d\u0438\u043a\u0430",
    },
    "vocab.update.current_label": {
        "uz": "Joriy versiya",
        "en": "Current version",
        "ru": "\u0422\u0435\u043a\u0443\u0449\u0430\u044f \u0432\u0435\u0440\u0441\u0438\u044f",
    },
    "vocab.update.new_label": {
        "uz": "Yangi versiya",
        "en": "New version",
        "ru": "\u041d\u043e\u0432\u0430\u044f \u0432\u0435\u0440\u0441\u0438\u044f",
    },
    "vocab.update.prompt": {
        "uz": "Qaysi versiyani saqlashni xohlaysiz?",
        "en": "Which version would you like to keep?",
        "ru": "\u041a\u0430\u043a\u0443\u044e \u0432\u0435\u0440\u0441\u0438\u044e \u0432\u044b \u0445\u043e\u0442\u0438\u0442\u0435 \u043e\u0441\u0442\u0430\u0432\u0438\u0442\u044c?",
    },
    "vocab.update_no_longer_available": {
        "uz": "Yangilanish endi mavjud emas.",
        "en": "This update is no longer available.",
        "ru": "\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u0431\u043e\u043b\u044c\u0448\u0435 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e.",
    },
    # ---- answer / toast strings (shown via callback.answer) ----
    "vocab.answer_favorited": {
        "uz": "\u2b50 Sevimlilar ro'yxatiga qo'shildi",
        "en": "\u2b50 Added to favorites",
        "ru": "\u2b50 \u0414\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u043e \u0432 \u0438\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0435",
    },
    "vocab.answer_unfavorited": {
        "uz": "Sevimlilardan olib tashlandi",
        "en": "Removed from favorites",
        "ru": "\u0423\u0431\u0440\u0430\u043d\u043e \u0438\u0437 \u0438\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0433\u043e",
    },
    "vocab.answer_deleted": {
        "uz": "\U0001f5d1 So'z lug'atdan o'chirildi",
        "en": "\U0001f5d1 Word removed from vocabulary",
        "ru": "\U0001f5d1 \u0421\u043b\u043e\u0432\u043e \u0443\u0434\u0430\u043b\u0435\u043d\u043e \u0438\u0437 \u0441\u043b\u043e\u0432\u0430\u0440\u044f",
    },
    "vocab.answer_updated": {
        "uz": "\u2728 Mnemonika yangilandi!",
        "en": "\u2728 Mnemonic updated!",
        "ru": "\u2728 \u041c\u043d\u0435\u043c\u043e\u043d\u0438\u043a\u0430 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0430!",
    },
    "vocab.answer_kept_current": {
        "uz": "Joriy versiya saqlandi",
        "en": "Keeping current version",
        "ru": "\u041e\u0441\u0442\u0430\u0451\u043c\u0441\u044f \u043d\u0430 \u0442\u0435\u043a\u0443\u0449\u0435\u0439 \u0432\u0435\u0440\u0441\u0438\u0438",
    },
    # ---- button labels ----
    "vocab.btn.search": {
        "uz": "\U0001f50d Qidirish",
        "en": "\U0001f50d Search",
        "ru": "\U0001f50d \u041f\u043e\u0438\u0441\u043a",
    },
    "vocab.btn.clear_search": {
        "uz": "\u274c Filtrni tozalash",
        "en": "\u274c Clear filter",
        "ru": "\u274c \u0421\u0431\u0440\u043e\u0441\u0438\u0442\u044c \u0444\u0438\u043b\u044c\u0442\u0440",
    },
    "vocab.btn.cancel_search": {
        "uz": "\u274c Bekor qilish",
        "en": "\u274c Cancel",
        "ru": "\u274c \u041e\u0442\u043c\u0435\u043d\u0430",
    },
    "vocab.btn.prev": {
        "uz": "\u2b05 Oldingi",
        "en": "\u2b05 Prev",
        "ru": "\u2b05 \u041d\u0430\u0437\u0430\u0434",
    },
    "vocab.btn.next": {
        "uz": "Keyingi \u27a1",
        "en": "Next \u27a1",
        "ru": "\u0414\u0430\u043b\u0435\u0435 \u27a1",
    },
    "vocab.btn.prev_word": {
        "uz": "\u25c0 Oldingi so'z",
        "en": "\u25c0 Prev word",
        "ru": "\u25c0 \u041f\u0440\u0435\u0434. \u0441\u043b\u043e\u0432\u043e",
    },
    "vocab.btn.next_word": {
        "uz": "Keyingi so'z \u25ba",
        "en": "Next word \u25ba",
        "ru": "\u0421\u043b\u0435\u0434. \u0441\u043b\u043e\u0432\u043e \u25ba",
    },
    "vocab.btn.favorite": {
        "uz": "\u2b50 Sevimlilarga qo'shish",
        "en": "\u2b50 Add to favorites",
        "ru": "\u2b50 \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0432 \u0438\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0435",
    },
    "vocab.btn.unfavorite": {
        "uz": "\u2b50 Sevimlilardan olib tashlash",
        "en": "\u2b50 Remove from favorites",
        "ru": "\u2b50 \u0423\u0431\u0440\u0430\u0442\u044c \u0438\u0437 \u0438\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0433\u043e",
    },
    "vocab.btn.delete": {
        "uz": "\U0001f5d1 O'chirish",
        "en": "\U0001f5d1 Delete",
        "ru": "\U0001f5d1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c",
    },
    "vocab.btn.delete_confirm": {
        "uz": "\u2705 Ha, o'chirish",
        "en": "\u2705 Yes, delete",
        "ru": "\u2705 \u0414\u0430, \u0443\u0434\u0430\u043b\u0438\u0442\u044c",
    },
    "vocab.btn.delete_cancel": {
        "uz": "\u274c Bekor qilish",
        "en": "\u274c Cancel",
        "ru": "\u274c \u041e\u0442\u043c\u0435\u043d\u0430",
    },
    "vocab.btn.back_to_list": {
        "uz": "\u2b05 Lug'atga qaytish",
        "en": "\u2b05 Back to vocabulary",
        "ru": "\u2b05 \u041d\u0430\u0437\u0430\u0434 \u043a \u0441\u043b\u043e\u0432\u0430\u0440\u044e",
    },
    "vocab.btn.back_to_word": {
        "uz": "\u2b05 So'zga qaytish",
        "en": "\u2b05 Back to word",
        "ru": "\u2b05 \u041d\u0430\u0437\u0430\u0434 \u043a \u0441\u043b\u043e\u0432\u0443",
    },
    "vocab.btn.view_update": {
        "uz": "\u2728 Yangi mnemonikani ko'rish",
        "en": "\u2728 View new mnemonic",
        "ru": "\u2728 \u041f\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c \u043d\u043e\u0432\u0443\u044e \u043c\u043d\u0435\u043c\u043e\u043d\u0438\u043a\u0443",
    },
    "vocab.btn.accept_update": {
        "uz": "\u2728 Yangi versiyani qabul qilish",
        "en": "\u2728 Update Mnemonic",
        "ru": "\u2728 \u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u043c\u043d\u0435\u043c\u043e\u043d\u0438\u043a\u0443",
    },
    "vocab.btn.keep_current": {
        "uz": "Hozirgi versiyani saqlash",
        "en": "Keep Current",
        "ru": "\u041e\u0441\u0442\u0430\u0432\u0438\u0442\u044c \u0442\u0435\u043a\u0443\u0449\u0443\u044e",
    },

    # ── AI Chat (Feature A) — additive, no existing keys changed ─────────
    "btn_ai_chat": {
        "uz": "🤖 AI Suhbat",
        "en": "🤖 AI Chat",
        "ru": "🤖 ИИ-чат",
    },
    "ai_chat.welcome": {
        "uz": (
            "🤖 <b>AI Suhbat</b>\n\n"
            "Men sizning shaxsiy o'qish yordamchingizman. "
            "Ingliz tili, grammatika, lug'at, IELTS yoki har qanday savol bo'yicha yozing.\n\n"
            "💡 Suhbatni tugatish uchun /end yoki tugmani bosing."
        ),
        "en": (
            "🤖 <b>AI Chat</b>\n\n"
            "I'm your personal learning assistant. "
            "Ask me anything about English, grammar, vocabulary, IELTS, or any topic.\n\n"
            "💡 Type /end or tap the button to end the session."
        ),
        "ru": (
            "🤖 <b>ИИ-чат</b>\n\n"
            "Я ваш персональный помощник по обучению. "
            "Спрашивайте о чём угодно: английский, грамматика, словарный запас, IELTS.\n\n"
            "💡 Введите /end или нажмите кнопку, чтобы завершить сессию."
        ),
    },
    "ai_chat.thinking": {
        "uz": "🤔 O'ylayapman...",
        "en": "🤔 Thinking...",
        "ru": "🤔 Думаю...",
    },
    "ai_chat.error": {
        "uz": "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
        "en": "❌ Something went wrong. Please try again.",
        "ru": "❌ Что-то пошло не так. Попробуйте ещё раз.",
    },
    "ai_chat.session_ended": {
        "uz": "✅ Suhbat yakunlandi. Bosh sahifaga qaytdingiz.",
        "en": "✅ Session ended. Returned to home.",
        "ru": "✅ Сессия завершена. Возврат на главную.",
    },
    "ai_chat.new_session": {
        "uz": "🔄 Yangi suhbat boshlandi.",
        "en": "🔄 New session started.",
        "ru": "🔄 Новая сессия началась.",
    },
    "ai_chat.no_router": {
        "uz": "⚠️ AI xizmat hozirda mavjud emas. Iltimos, keyinroq urinib ko'ring.",
        "en": "⚠️ AI service is unavailable right now. Please try again later.",
        "ru": "⚠️ Сервис ИИ временно недоступен. Попробуйте позже.",
    },
    "ai_chat.btn_end": {
        "uz": "❌ Suhbatni tugatish",
        "en": "❌ End Chat",
        "ru": "❌ Завершить чат",
    },
    "ai_chat.btn_new": {
        "uz": "🔄 Yangi suhbat",
        "en": "🔄 New Chat",
        "ru": "🔄 Новый чат",
    },

    # ── Quiz (Feature C) — additive, no existing keys changed ────────────
    "btn_quiz": {
        "uz": "🧠 Quiz",
        "en": "🧠 Quiz",
        "ru": "🧠 Квиз",
    },
    "quiz.welcome": {
        "uz": "🧠 <b>Quiz</b>\n\nQanday tur quiz o'ynashni xohlaysiz?",
        "en": "🧠 <b>Quiz</b>\n\nWhat type of quiz would you like?",
        "ru": "🧠 <b>Квиз</b>\n\nКакой тип квиза вы хотите?",
    },
    "quiz.generating": {
        "uz": "⚙️ Quiz tayyorlanmoqda...",
        "en": "⚙️ Generating your quiz...",
        "ru": "⚙️ Генерирую квиз...",
    },
    "quiz.question_header": {
        "uz": "❓ Savol {current}/{total}",
        "en": "❓ Question {current}/{total}",
        "ru": "❓ Вопрос {current}/{total}",
    },
    "quiz.results": {
        "uz": (
            "🏆 <b>Quiz yakunlandi!</b>\n\n"
            "📊 Natija: <b>{correct}/{total}</b>\n"
            "✅ To'g'ri: {correct}\n"
            "❌ Noto'g'ri: {wrong}\n"
            "🎯 Aniqlik: {accuracy}%\n"
            "⏱ Vaqt: {time}s"
        ),
        "en": (
            "🏆 <b>Quiz Complete!</b>\n\n"
            "📊 Score: <b>{correct}/{total}</b>\n"
            "✅ Correct: {correct}\n"
            "❌ Wrong: {wrong}\n"
            "🎯 Accuracy: {accuracy}%\n"
            "⏱ Time: {time}s"
        ),
        "ru": (
            "🏆 <b>Квиз завершён!</b>\n\n"
            "📊 Результат: <b>{correct}/{total}</b>\n"
            "✅ Правильно: {correct}\n"
            "❌ Неправильно: {wrong}\n"
            "🎯 Точность: {accuracy}%\n"
            "⏱ Время: {time}с"
        ),
    },
    "quiz.weak_topics": {
        "uz": "📝 Takrorlash kerak: {words}",
        "en": "📝 Review these: {words}",
        "ru": "📝 Повторить: {words}",
    },
    "quiz.error": {
        "uz": "❌ Quiz yaratishda xato. Iltimos, qayta urinib ko'ring.",
        "en": "❌ Failed to generate quiz. Please try again.",
        "ru": "❌ Не удалось создать квиз. Попробуйте ещё раз.",
    },
    "quiz.no_router": {
        "uz": "⚠️ AI xizmat hozirda mavjud emas.",
        "en": "⚠️ AI service is unavailable right now.",
        "ru": "⚠️ Сервис ИИ временно недоступен.",
    },
    "quiz.no_vocabulary": {
        "uz": "📚 Quiz uchun so'zlar yetarli emas. Avval bir nechta so'z qidiring.",
        "en": "📚 Not enough vocabulary for a quiz. Search for some words first.",
        "ru": "📚 Недостаточно слов для квиза. Сначала найдите несколько слов.",
    },
    "quiz.not_enough_vocab": {
        "uz": "📚 Lug'atingizda faqat {count} ta so'z bor. Lug'at quizi uchun kamida {min} ta so'z kerak.\n\nAvval ko'proq so'z qidiring yoki boshqa quiz turini tanlang.",
        "en": "📚 Your vocabulary has only {count} word(s). A vocabulary quiz needs at least {min} words.\n\nSearch for more words first, or choose a different quiz type.",
        "ru": "📚 В вашем словаре только {count} слов(а). Для словарного квиза нужно минимум {min} слов.\n\nСначала найдите больше слов или выберите другой тип квиза.",
    },
    "quiz.listening_coming_soon": {
        "uz": "🎧 Tinglash quizi tez orada chiqadi!\n\nBoshqa quiz turini tanlang.",
        "en": "🎧 Listening Quiz is coming soon!\n\nPlease choose a different quiz type for now.",
        "ru": "🎧 Квиз на аудирование скоро будет!\n\nПожалуйста, выберите другой тип квиза.",
    },
    "quiz.reading_passage": {
        "uz": "📖 <b>Matn:</b>\n\n{passage}\n\n<i>Matnni o'qib chiqing, so'ng savollarni boshlang.</i>",
        "en": "📖 <b>Passage:</b>\n\n{passage}\n\n<i>Read the passage above, then start the questions.</i>",
        "ru": "📖 <b>Текст:</b>\n\n{passage}\n\n<i>Прочитайте текст выше, затем начните вопросы.</i>",
    },
    "quiz.aborted": {
        "uz": "✅ Quiz to'xtatildi.",
        "en": "✅ Quiz ended.",
        "ru": "✅ Квиз завершён.",
    },
    "quiz.btn.vocabulary": {
        "uz": "📚 Lug'at",
        "en": "📚 Vocabulary",
        "ru": "📚 Словарь",
    },
    "quiz.btn.grammar": {
        "uz": "📝 Grammatika",
        "en": "📝 Grammar",
        "ru": "📝 Грамматика",
    },
    "quiz.btn.gap_fill": {
        "uz": "✏️ Bo'sh joy",
        "en": "✏️ Gap Fill",
        "ru": "✏️ Пропуск",
    },
    "quiz.btn.reading": {
        "uz": "📖 O'qish",
        "en": "📖 Reading",
        "ru": "📖 Чтение",
    },
    "quiz.btn.listening": {
        "uz": "🎧 Tinglash",
        "en": "🎧 Listening",
        "ru": "🎧 Аудирование",
    },
    "quiz.btn.mixed": {
        "uz": "🎲 Aralash",
        "en": "🎲 Mixed",
        "ru": "🎲 Смешанный",
    },
    "quiz.btn.end": {
        "uz": "⛔ Quizni to'xtatish",
        "en": "⛔ End Quiz",
        "ru": "⛔ Завершить квиз",
    },
    "quiz.btn.new_quiz": {
        "uz": "🔄 Yangi quiz",
        "en": "🔄 New Quiz",
        "ru": "🔄 Новый квиз",
    },
    "quiz.btn.reading_start": {
        "uz": "▶️ Savollarni boshlash",
        "en": "▶️ Start Questions",
        "ru": "▶️ Начать вопросы",
    },
    # Legacy button keys kept for backward compatibility
    "quiz.btn.meaning": {
        "uz": "📖 Ma'no",
        "en": "📖 Meaning",
        "ru": "📖 Значение",
    },
    "quiz.btn.synonym": {
        "uz": "🔄 Sinonim",
        "en": "🔄 Synonym",
        "ru": "🔄 Синоним",
    },
    "quiz.btn.document": {
        "uz": "📄 Hujjat",
        "en": "📄 Document",
        "ru": "📄 Документ",
    },

    # ── Learn section ──────────────────────────────────────────────────── #
    "btn_learn": {
        "uz": "📚 O'rganish",
        "en": "📚 Learn",
        "ru": "📚 Учиться",
    },
    "learn.welcome": {
        "uz": "📚 <b>O'rganish bo'limi</b>\n\nNimani o'rganmoqchisiz?",
        "en": "📚 <b>Learn</b>\n\nWhat would you like to study?",
        "ru": "📚 <b>Обучение</b>\n\nЧто вы хотите изучить?",
    },
    "learn.btn.grammar": {
        "uz": "📖 Grammatika",
        "en": "📖 Grammar",
        "ru": "📖 Грамматика",
    },
    # ── Grammar Learning ───────────────────────────────────────────────── #
    "grammar.topics_title": {
        "uz": "📘 <b>Grammatika mavzulari</b>\n\nQaysi mavzuni o'rganmoqchisiz?",
        "en": "📘 <b>Grammar Topics</b>\n\nWhich topic would you like to study?",
        "ru": "📘 <b>Темы грамматики</b>\n\nКакую тему вы хотите изучить?",
    },
    "grammar.no_topics": {
        "uz": "📭 Hozircha grammatika mavzulari yo'q. Iltimos, keyinroq qaytib keling.",
        "en": "📭 No grammar topics available yet. Please check back later.",
        "ru": "📭 Пока нет тем по грамматике. Пожалуйста, зайдите позже.",
    },
    "grammar.lesson_header": {
        "uz": "📖 <b>{title}</b>",
        "en": "📖 <b>{title}</b>",
        "ru": "📖 <b>{title}</b>",
    },
    "grammar.lesson_error": {
        "uz": "⚠️ Darslikni yuklashda xato yuz berdi. Iltimos, keyinroq urinib ko'ring.",
        "en": "⚠️ Could not load the lesson. Please try again later.",
        "ru": "⚠️ Не удалось загрузить урок. Пожалуйста, попробуйте позже.",
    },
    "grammar.lesson_not_configured": {
        "uz": "⚠️ Bu mavzu uchun darslik hali konfiguratsiya qilinmagan.",
        "en": "⚠️ This topic's lesson has not been configured yet.",
        "ru": "⚠️ Урок по этой теме ещё не настроен.",
    },
    "grammar.channel_not_configured": {
        "uz": "⚠️ Grammar kanal konfiguratsiya qilinmagan. Administrator bilan bog'laning.",
        "en": "⚠️ Grammar channel is not configured. Please contact the administrator.",
        "ru": "⚠️ Канал грамматики не настроен. Обратитесь к администратору.",
    },
    "grammar.ask_ai_prompt": {
        "uz": "❓ <b>{title}</b> haqida savolingizni yozing:",
        "en": "❓ Ask your question about <b>{title}</b>:",
        "ru": "❓ Задайте ваш вопрос о <b>{title}</b>:",
    },
    "grammar.ask_ai_thinking": {
        "uz": "🤔 O'ylayapman...",
        "en": "🤔 Thinking...",
        "ru": "🤔 Думаю...",
    },
    "grammar.ask_ai_error": {
        "uz": "⚠️ Javob olishda xato. Iltimos, qayta urinib ko'ring.",
        "en": "⚠️ Could not get an answer. Please try again.",
        "ru": "⚠️ Не удалось получить ответ. Пожалуйста, попробуйте снова.",
    },
    "grammar.quiz_generating": {
        "uz": "⚙️ Quiz tayyorlanmoqda...",
        "en": "⚙️ Generating quiz...",
        "ru": "⚙️ Генерирую квиз...",
    },
    "grammar.quiz_error": {
        "uz": "⚠️ Quiz yaratishda xato. Iltimos, qayta urinib ko'ring.",
        "en": "⚠️ Could not generate the quiz. Please try again.",
        "ru": "⚠️ Не удалось создать квиз. Пожалуйста, попробуйте снова.",
    },
    "grammar.quiz_results": {
        "uz": "📊 <b>Natijalar</b>\n\n✅ To'g'ri: {correct}/{total}\n📈 Aniqlik: {accuracy}%\n🎯 Mahorat: {mastery}%",
        "en": "📊 <b>Results</b>\n\n✅ Correct: {correct}/{total}\n📈 Accuracy: {accuracy}%\n🎯 Mastery: {mastery}%",
        "ru": "📊 <b>Результаты</b>\n\nCorrect: {correct}/{total}\n📈 Точность: {accuracy}%\n🎯 Мастерство: {mastery}%",
    },
    "grammar.quiz_completed_status": {
        "uz": "🏆 Siz bu mavzuni o'zlashtirdingiz!",
        "en": "🏆 You have mastered this topic!",
        "ru": "🏆 Вы освоили эту тему!",
    },
    "grammar.btn.ask_ai": {
        "uz": "❓ AI dan so'rash",
        "en": "❓ Ask AI",
        "ru": "❓ Спросить AI",
    },
    "grammar.btn.test": {
        "uz": "🧠 O'zingni sinab ko'r",
        "en": "🧠 Test Yourself",
        "ru": "🧠 Проверь себя",
    },
    "grammar.btn.back_topics": {
        "uz": "⬅️ Mavzularga qaytish",
        "en": "⬅️ Back to Grammar",
        "ru": "⬅️ Назад к темам",
    },
    "grammar.btn.stop_asking": {
        "uz": "🔙 Darslikka qaytish",
        "en": "🔙 Back to Lesson",
        "ru": "🔙 Вернуться к уроку",
    },
    "grammar.btn.test_again": {
        "uz": "🔄 Qayta sinash",
        "en": "🔄 Test Again",
        "ru": "🔄 Пройти снова",
    },
    "btn_home": {
        "uz": "🏠 Bosh sahifa",
        "en": "🏠 Home",
        "ru": "🏠 Главная",
    },

    # ── Admin: Grammar Lessons management ─────────────────────────────── #
    "admin.btn.grammar_lessons": {
        "uz": "📚 Grammar Darslar",
        "en": "📚 Grammar Lessons",
        "ru": "📚 Уроки грамматики",
    },
    "admin.grammar.menu_title": {
        "uz": "📚 <b>Grammar Darslar boshqaruvi</b>\n\nJami: {total} ta dars",
        "en": "📚 <b>Grammar Lessons Management</b>\n\nTotal: {total} lessons",
        "ru": "📚 <b>Управление уроками грамматики</b>\n\nВсего: {total} уроков",
    },
    "admin.grammar.btn.add_forward": {
        "uz": "➕ Dars qo\'shish (forward)",
        "en": "➕ Add Lesson (forward)",
        "ru": "➕ Добавить урок (форвард)",
    },
    "admin.grammar.btn.add_manual": {
        "uz": "⌨️ Dars qo\'shish (ID)",
        "en": "⌨️ Add Lesson (ID)",
        "ru": "⌨️ Добавить урок (ID)",
    },
    "admin.grammar.btn.list": {
        "uz": "📋 Barcha darslar",
        "en": "📋 All Lessons",
        "ru": "📋 Все уроки",
    },
    "admin.grammar.btn.back": {
        "uz": "⬅️ Admin menyuga",
        "en": "⬅️ Admin Menu",
        "ru": "⬅️ Меню администратора",
    },
    "admin.grammar.btn.edit": {
        "uz": "✏️ Tahrirlash",
        "en": "✏️ Edit",
        "ru": "✏️ Редактировать",
    },
    "admin.grammar.btn.toggle_enable": {
        "uz": "🟢 Yoqish",
        "en": "🟢 Enable",
        "ru": "🟢 Включить",
    },
    "admin.grammar.btn.toggle_disable": {
        "uz": "🔴 O\'chirish",
        "en": "🔴 Disable",
        "ru": "🔴 Отключить",
    },
    "admin.grammar.btn.delete": {
        "uz": "🗑 O\'chirish",
        "en": "🗑 Delete",
        "ru": "🗑 Удалить",
    },
    "admin.grammar.btn.move_up": {
        "uz": "⬆️ Yuqoriga",
        "en": "⬆️ Move Up",
        "ru": "⬆️ Вверх",
    },
    "admin.grammar.btn.move_down": {
        "uz": "⬇️ Pastga",
        "en": "⬇️ Move Down",
        "ru": "⬇️ Вниз",
    },
    "admin.grammar.btn.edit_name": {
        "uz": "📝 Nomni o\'zgartirish",
        "en": "📝 Edit Name",
        "ru": "📝 Изменить название",
    },
    "admin.grammar.btn.edit_button": {
        "uz": "🔘 Tugma nomini o\'zgartirish",
        "en": "🔘 Edit Button Name",
        "ru": "🔘 Изменить название кнопки",
    },
    "admin.grammar.btn.edit_msgid": {
        "uz": "🔗 Xabar ID\'ni o\'zgartirish",
        "en": "🔗 Edit Message ID",
        "ru": "🔗 Изменить ID сообщения",
    },
    "admin.grammar.btn.confirm_delete": {
        "uz": "✅ Ha, o\'chirish",
        "en": "✅ Yes, Delete",
        "ru": "✅ Да, удалить",
    },
    "admin.grammar.btn.cancel": {
        "uz": "❌ Bekor qilish",
        "en": "❌ Cancel",
        "ru": "❌ Отмена",
    },
    "admin.grammar.prompt_forward": {
        "uz": "📤 Grammar kanalidan darslikni forward qiling yoki xabar ID kiriting:",
        "en": "📤 Forward the grammar lesson from the configured channel, or enter a message ID:",
        "ru": "📤 Перешлите урок грамматики из настроенного канала или введите ID сообщения:",
    },
    "admin.grammar.prompt_manual_id": {
        "uz": "⌨️ Grammar kanali xabar ID\'sini kiriting (raqam):",
        "en": "⌨️ Enter the message ID from the grammar channel (number):",
        "ru": "⌨️ Введите ID сообщения из канала грамматики (число):",
    },
    "admin.grammar.prompt_topic_name": {
        "uz": "📝 Grammatika mavzusi nomini kiriting:\nMisol: Present Perfect",
        "en": "📝 Enter the grammar topic name:\nExample: Present Perfect",
        "ru": "📝 Введите название темы грамматики:\nПример: Present Perfect",
    },
    "admin.grammar.prompt_button_name": {
        "uz": "🔘 Tugma nomini kiriting (yoki /skip bosing):\nMisol: 🟢 Present Perfect",
        "en": "🔘 Enter the button name (or send /skip to use topic name):\nExample: 🟢 Present Perfect",
        "ru": "🔘 Введите название кнопки (или /skip для использования названия темы):\nПример: 🟢 Present Perfect",
    },
    "admin.grammar.added": {
        "uz": "✅ Grammar darsi muvaffaqiyatli qo\'shildi!\n\n📖 Mavzu: {title}\n🔘 Tugma: {button_name}\n🔗 Xabar ID: {message_id}\n📊 Holat: Faol",
        "en": "✅ Grammar lesson added successfully!\n\n📖 Topic: {title}\n🔘 Button: {button_name}\n🔗 Message ID: {message_id}\n📊 Status: Active",
        "ru": "✅ Урок грамматики успешно добавлен!\n\n📖 Тема: {title}\n🔘 Кнопка: {button_name}\n🔗 ID сообщения: {message_id}\n📊 Статус: Активен",
    },
    "admin.grammar.list_empty": {
        "uz": "📭 Hozircha grammar darslar yo\'q.",
        "en": "📭 No grammar lessons yet.",
        "ru": "📭 Уроков грамматики пока нет.",
    },
    "admin.grammar.topic_card": {
        "uz": "#{id} {status} <b>{title}</b>\n🔘 {button_name}\n🔗 msg_id: {message_id}\n📊 Tartib: {order}",
        "en": "#{id} {status} <b>{title}</b>\n🔘 {button_name}\n🔗 msg_id: {message_id}\n📊 Order: {order}",
        "ru": "#{id} {status} <b>{title}</b>\n🔘 {button_name}\n🔗 msg_id: {message_id}\n📊 Порядок: {order}",
    },
    "admin.grammar.enabled": {
        "uz": "🟢 Dars yoqildi: {title}",
        "en": "🟢 Lesson enabled: {title}",
        "ru": "🟢 Урок включён: {title}",
    },
    "admin.grammar.disabled": {
        "uz": "🔴 Dars o\'chirildi: {title}",
        "en": "🔴 Lesson disabled: {title}",
        "ru": "🔴 Урок отключён: {title}",
    },
    "admin.grammar.confirm_delete_prompt": {
        "uz": "⚠️ <b>{title}</b> ni o\'chirishga ishonchingiz komilmi?\n\nFoydalanuvchi progressi saqlanib qoladi.",
        "en": "⚠️ Are you sure you want to delete <b>{title}</b>?\n\nUser progress will be preserved.",
        "ru": "⚠️ Вы уверены, что хотите удалить <b>{title}</b>?\n\nПрогресс пользователей будет сохранён.",
    },
    "admin.grammar.deleted": {
        "uz": "🗑 Dars o\'chirildi: {title}",
        "en": "🗑 Lesson deleted: {title}",
        "ru": "🗑 Урок удалён: {title}",
    },
    "admin.grammar.delete_cancelled": {
        "uz": "❌ O\'chirish bekor qilindi.",
        "en": "❌ Deletion cancelled.",
        "ru": "❌ Удаление отменено.",
    },
    "admin.grammar.moved": {
        "uz": "↕️ Tartib o\'zgartirildi.",
        "en": "↕️ Order updated.",
        "ru": "↕️ Порядок обновлён.",
    },
    "admin.grammar.edit_menu": {
        "uz": "✏️ Nima o\'zgartirmoqchisiz?\n\n<b>{title}</b>",
        "en": "✏️ What would you like to edit?\n\n<b>{title}</b>",
        "ru": "✏️ Что хотите изменить?\n\n<b>{title}</b>",
    },
    "admin.grammar.prompt_new_name": {
        "uz": "📝 Yangi mavzu nomini kiriting:",
        "en": "📝 Enter the new topic name:",
        "ru": "📝 Введите новое название темы:",
    },
    "admin.grammar.prompt_new_button": {
        "uz": "🔘 Yangi tugma nomini kiriting:",
        "en": "🔘 Enter the new button name:",
        "ru": "🔘 Введите новое название кнопки:",
    },
    "admin.grammar.prompt_new_msgid": {
        "uz": "🔗 Yangi xabar ID kiriting yoki yangi postni forward qiling:",
        "en": "🔗 Enter a new message ID or forward the new channel post:",
        "ru": "🔗 Введите новый ID сообщения или перешлите новый пост из канала:",
    },
    "admin.grammar.updated": {
        "uz": "✅ Dars yangilandi: {title}",
        "en": "✅ Lesson updated: {title}",
        "ru": "✅ Урок обновлён: {title}",
    },
    "admin.grammar.error.wrong_channel": {
        "uz": "❌ Bu post konfiguratsiya qilingan grammar kanalidan emas.\nChannel ID: {expected}",
        "en": "❌ This post is not from the configured grammar channel.\nExpected channel: {expected}",
        "ru": "❌ Этот пост не из настроенного канала грамматики.\nОжидаемый канал: {expected}",
    },
    "admin.grammar.error.duplicate_msg_id": {
        "uz": "⚠️ Bu xabar ID allaqachon ro\'yxatdan o\'tgan.",
        "en": "⚠️ This message ID is already registered.",
        "ru": "⚠️ Этот ID сообщения уже зарегистрирован.",
    },
    "admin.grammar.error.channel_not_configured": {
        "uz": "❌ GRAMMAR_CHANNEL_ID sozlanmagan. .env faylini tekshiring.",
        "en": "❌ GRAMMAR_CHANNEL_ID is not configured. Check your .env file.",
        "ru": "❌ GRAMMAR_CHANNEL_ID не настроен. Проверьте файл .env.",
    },
    "admin.grammar.error.invalid_msg_id": {
        "uz": "❌ Noto\'g\'ri xabar ID. Faqat raqam kiriting.",
        "en": "❌ Invalid message ID. Please enter a number only.",
        "ru": "❌ Неверный ID сообщения. Введите только число.",
    },
    "admin.grammar.error.msg_not_found": {
        "uz": "❌ Kanal xabari topilmadi. ID ni tekshiring va bot kanal a\'zosi ekanligini tekshiring.",
        "en": "❌ Channel message not found. Check the ID and that the bot is a channel member.",
        "ru": "❌ Сообщение в канале не найдено. Проверьте ID и убедитесь, что бот является участником канала.",
    },
    "admin.grammar.error.general": {
        "uz": "❌ Xato yuz berdi. Iltimos, qayta urinib ko\'ring.",
        "en": "❌ An error occurred. Please try again.",
        "ru": "❌ Произошла ошибка. Пожалуйста, попробуйте снова.",
    },
    "admin.grammar.channel_not_configured_user": {
        "uz": "❌ Bu grammar darsi vaqtincha mavjud emas.",
        "en": "❌ This grammar lesson is temporarily unavailable.",
        "ru": "❌ Этот урок грамматики временно недоступен.",
    },

}


def t(key: str, lang: str = "uz", **kwargs: str) -> str:
    """Look up a localised string by key, format it with kwargs if given.

    Fallback order: requested lang → English → Uzbek → raw key.
    This satisfies the spec requirement: "If a user has an invalid language,
    automatically fallback to English."
    """
    entry = MESSAGES.get(key)
    if entry is None:
        return key
    template = entry.get(lang) or entry.get("en") or entry.get("uz") or key
    return template.format(**kwargs) if kwargs else template
