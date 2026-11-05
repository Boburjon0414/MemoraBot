from pathlib import Path
import edge_tts


class PronunciationService:

    async def generate_voice(self, word: str, lang: str) -> str:
        project_root = Path(__file__).resolve().parents[2]

        temp_dir = project_root / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        audio_path = temp_dir / f"{word}.ogg"

        communicate = edge_tts.Communicate(word, lang)
        await communicate.save(str(audio_path))

        return str(audio_path)