

import os

from aiogram import F, Router
from aiogram.types import FSInputFile
from app.services import pronunciation_service
from app.services import settings_service
from app.services.mnemonic_service import MnemonicService
from app.services.pronunciation_service import PronunciationService
from app.services.user_service import UserService
from aiogram.types import CallbackQuery
from app.texts.messages import t
from app.services.settings_service import SettingsService
from app.keyboards.callback_data import MneVocaCallback




print("Pronunciation handler loaded successfully.")

router = Router(name="pronunciation")


@router.callback_query(MneVocaCallback.filter(F.action == "pronunciation"))
async def generate_pronunciation(
    callback: CallbackQuery,
    callback_data: MneVocaCallback,
    pronunciation_service: PronunciationService,
    mnemonic_service: MnemonicService,
    user_service: UserService,
    settings_service: SettingsService,
) -> None:
    """Generate pronunciation audio for a mnemonic word."""

    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer()
        return

    mnemonic = await mnemonic_service.get_by_id(callback_data.mnemonic_id)
    if mnemonic is None:
        await callback.answer("Mnemonic not found.")
        return

    voice_path = await pronunciation_service.generate_voice(
        word=mnemonic.word,
        lang="en-US-JennyNeural",
    )

    voice_file = FSInputFile(voice_path)
    lang = await settings_service.get_language(callback.from_user.id)
    
    try:
        await callback.message.answer_voice(
        voice=voice_file,
        caption=f"Pronunciation for <b><i>{mnemonic.word}</i></b>\n\n{t('pron_cap', lang)}",
        parse_mode="HTML",
        )
    finally:
        if os.path.exists(voice_path):
            os.remove(voice_path)
            