"""
STT Service — Speech-to-Text (giọng nói → văn bản).

Provider: openai | phowhisper | whisper.
- openai: dùng API transcribe của OpenAI (model gpt-transcribe).
- phowhisper/whisper: chạy model local, lazy-load.
"""
from app.config import (
    STT_PROVIDER, STT_MODEL, STT_PHOWHISPER_MODEL, STT_OPENAI_MODEL, OPENAI_API_KEY,
)


class STTService:
    def __init__(self):
        self.provider = STT_PROVIDER
        self._model = None
        self._error: str | None = None

    def load_model(self):
        """(Chỉ cho provider local) Lazy-load model STT."""
        if self.provider == "openai":
            return  # openai dùng API, không cần load model
        if self._model is not None or self._error is not None:
            return
        try:
            if self.provider == "phowhisper":
                from transformers import pipeline
                self._model = pipeline(
                    "automatic-speech-recognition",
                    model=STT_PHOWHISPER_MODEL,
                )
            elif self.provider == "whisper":
                import whisper
                self._model = whisper.load_model(STT_MODEL)
            else:
                self._error = f"Provider {self.provider} chưa được hỗ trợ"
        except Exception as e:  # noqa: BLE001
            self._error = str(e)

    @property
    def available(self) -> bool:
        if self.provider == "openai":
            return bool(OPENAI_API_KEY)
        self.load_model()
        return self._error is None

    def transcribe(self, audio_path: str) -> str:
        """Chuyển file audio → text."""
        if self.provider == "openai":
            return self._transcribe_openai(audio_path)

        self.load_model()
        if self._error is not None:
            raise RuntimeError(f"STT unavailable: {self._error}")
        if self.provider == "phowhisper":
            return self._model(audio_path)["text"].strip()
        if self.provider == "whisper":
            return self._model.transcribe(audio_path, language="vi")["text"].strip()
        return ""

    def _transcribe_openai(self, audio_path: str) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        with open(audio_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model=STT_OPENAI_MODEL,
                file=f,
                language="vi",
            )
        return (transcription.text or "").strip()


stt_service = STTService()
