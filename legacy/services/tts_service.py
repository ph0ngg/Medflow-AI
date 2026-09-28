"""
Service Text-to-Speech (TTS).
Chuyển văn bản → giọng nói.
"""
import io
import tempfile
from pathlib import Path

from config import TTS_PROVIDER, TTS_LANG


class TTSService:
    """
    Interface cho Text-to-Speech.
    Hiện triển khai với Edge TTS (miễn phí). Có thể mở rộng: Google TTS, VITS.
    """

    def __init__(self):
        self.provider = TTS_PROVIDER
        self.lang = TTS_LANG

    def synthesize(self, text: str) -> bytes:
        """
        Chuyển text → audio bytes (mp3/wav).
        Returns:
            Audio dạng bytes.
        """
        if self.provider == "edge":
            return self._synthesize_edge(text)
        else:
            raise NotImplementedError(f"Provider {self.provider} chưa được hỗ trợ.")

    def _synthesize_edge(self, text: str) -> bytes:
        """Dùng Edge TTS (free, chất lượng tốt cho tiếng Việt)."""
        import edge_tts
        import asyncio

        voice = "vi-VN-NamMinhNeural"  # Giọng nam tiếng Việt
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)

        async def _run():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_file.name)

        asyncio.run(_run())

        with open(temp_file.name, "rb") as f:
            audio_bytes = f.read()

        Path(temp_file.name).unlink()  # Xóa file tạm
        return audio_bytes


# Singleton
tts_service = TTSService()
