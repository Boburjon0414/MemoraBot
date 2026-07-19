"""All user-facing strings, in Uzbek (default), English, and Russian.

Kept as a single flat dictionary rather than full gettext/babel tooling —
V1's string set is small enough that this stays easy to scan and edit, while
already being structured so a proper i18n library could replace it later
without touching any call site (every lookup goes through `t()`).
"""

from __future__ import annotations

from typing import Final

MESSAGES: Final[dict[str, dict[str, str]]] = {
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
}


def t(key: str, lang: str = "uz", **kwargs: str) -> str:
    """Look up a localized string by key, formatting it with `kwargs` if given.

    Falls back to Uzbek, then to the raw key itself, if a translation is missing.
    """
    entry = MESSAGES.get(key)
    if entry is None:
        return key
    template = entry.get(lang) or entry.get("uz") or key
    return template.format(**kwargs) if kwargs else template
