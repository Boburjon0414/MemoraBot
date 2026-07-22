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
        "uz": "🔄 Boshqa versiya yarating",
        "en": "🔄 Generate Another Mnemonic",
        "ru": "🔄 Сгенерировать другую версию",
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
