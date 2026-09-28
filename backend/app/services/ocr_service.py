"""
OCR Service — quét CCCD, trích xuất thông tin.

Provider: paddle (thật) | mock (demo). Với mock, trả về danh tính demo
để luồng prototype chạy được mà không cần model OCR nặng.
"""
import re

from app.config import OCR_PROVIDER


class OCRService:
    def __init__(self):
        self.provider = OCR_PROVIDER
        self._model = None
        self._error: str | None = None

    def load_model(self):
        if self._model is not None or self._error is not None:
            return
        try:
            from paddleocr import PaddleOCR
            self._model = PaddleOCR(lang="vi", use_angle_cls=True)
        except Exception as e:  # noqa: BLE001
            self._error = str(e)

    @property
    def available(self) -> bool:
        return self.provider == "mock" or self._model is not None

    def extract_info(self, image) -> dict:
        """
        Trích xuất thông tin CCCD.
        Returns: {"full_name": ..., "dob": ..., "cccd": ..., "address": ...}
        """
        if self.provider == "mock":
            # Demo: trả về danh tính mẫu (KHÔNG phải dữ liệu thật)
            return {
                "full_name": "Nguyễn Văn A",
                "dob": "15/03/1985",
                "cccd": "001085000001",
                "address": "Hà Nội",
            }

        self.load_model()
        if self._error is not None:
            return {"full_name": "", "dob": "", "cccd": "", "address": ""}

        try:
            import numpy as np
            result = self._model.ocr(np.array(image), cls=True)
            lines = [line[1][0] for line in result[0]] if result and result[0] else []
            text = "\n".join(lines)
            return self._parse_cccd_text(text)
        except Exception:
            return {"full_name": "", "dob": "", "cccd": "", "address": ""}

    @staticmethod
    def _parse_cccd_text(text: str) -> dict:
        info = {"full_name": "", "dob": "", "cccd": "", "address": ""}
        cccd_match = re.search(r"\b(\d{12})\b", text)
        if cccd_match:
            info["cccd"] = cccd_match.group(1)
        dob_match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
        if dob_match:
            info["dob"] = dob_match.group(1)
        return info


ocr_service = OCRService()
