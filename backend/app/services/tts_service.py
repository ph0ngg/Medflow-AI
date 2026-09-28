"""
TTS Service — Text-to-Speech (văn bản → giọng nói).

Provider: openai (gpt-4o-mini-tts) | edge (giọng Việt).
"""
import tempfile
from pathlib import Path

from app.config import (
    TTS_PROVIDER, TTS_LANG, TTS_OPENAI_MODEL, TTS_OPENAI_VOICE, OPENAI_API_KEY,
)


class TTSService:
    def __init__(self):
        self.provider = TTS_PROVIDER
        self.lang = TTS_LANG

    def synthesize(self, text: str) -> bytes:
        if self.provider == "openai":
            return self._synthesize_openai(text)
        if self.provider == "edge":
            return self._synthesize_edge(text)
        raise NotImplementedError(f"Provider {self.provider} chưa được hỗ trợ.")

    def _synthesize_openai(self, text: str) -> bytes:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.audio.speech.create(
            model=TTS_OPENAI_MODEL,
            voice=TTS_OPENAI_VOICE,
            input=text,
            instructions="Speak naturally, calmly, and clearly in Vietnamese."
        )
        return response.content

    def _synthesize_edge(self, text: str) -> bytes:
        import asyncio
        import edge_tts

        voice = "vi-VN-NamMinhNeural"
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)

        async def _run():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_file.name)

        try:
            asyncio.run(_run())
            with open(temp_file.name, "rb") as f:
                return f.read()
        finally:
            Path(temp_file.name).unlink(missing_ok=True)


tts_service = TTSService()
