"""
Service Speech-to-Text (STT).
Chuyển giọng nói → văn bản.

Hỗ trợ:
  - PhoWhisper (vinai/PhoWhisper-small): dùng transformers pipeline, tối ưu cho tiếng Việt.
  - Whisper (OpenAI): dùng thư viện openai-whisper.
"""
from config import STT_PROVIDER, STT_MODEL, STT_PHOWHISPER_MODEL


class STTService:
    """
    Interface cho Speech-to-Text.
    Hiện triển khai với Whisper (OpenAI). Có thể mở rộng: Google STT, Vosk.
    """

    def __init__(self):
        self.provider = STT_PROVIDER
        self._model = None

    def load_model(self):
        """Lazy load model để tránh khởi tạo khi import."""
        if self._model is not None:
            return

        if self.provider == "phowhisper":
            from transformers import pipeline
            # PhoWhisper yêu cầu audio 16kHz; pipeline tự xử lý resample
            self._model = pipeline(
                "automatic-speech-recognition",
                model=STT_PHOWHISPER_MODEL,
            )
        elif self.provider == "whisper":
            import whisper
            self._model = whisper.load_model(STT_MODEL)
        else:
            raise NotImplementedError(f"Provider {self.provider} chưa được hỗ trợ.")

    def transcribe(self, audio_path: str) -> str:
        """
        Chuyển file audio → text.
        Args:
            audio_path: Đường dẫn file audio (wav, mp3, etc.)
                             PhoWhisper yêu cầu sampling rate 16kHz.
        Returns:
            Chuỗi văn bản đã nhận dạng.
        """
        self.load_model()

        if self.provider == "phowhisper":
            # transformers pipeline trả về dict với key "text"
            return self._model(audio_path)["text"].strip()

        if self.provider == "whisper":
            result = self._model.transcribe(audio_path, language="vi")
            return result["text"].strip()

        return ""


# Singleton
stt_service = STTService()
