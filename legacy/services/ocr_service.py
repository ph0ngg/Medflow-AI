"""
Service OCR - Quét CCCD (Căn cước công dân).
Dùng PaddleOCR hoặc Tesseract để trích xuất thông tin từ ảnh CCCD.
"""
from config import OCR_PROVIDER


class OCRService:
    """
    Interface cho OCR. Hiện triển khai với PaddleOCR.
    """

    def __init__(self):
        self.provider = OCR_PROVIDER
        self._model = None

    def load_model(self):
        if self._model is not None:
            return
        if self.provider == "paddle":
            from paddleocr import PaddleOCR
            self._model = PaddleOCR(lang="vi", use_angle_cls=True)
        else:
            raise NotImplementedError(f"Provider {self.provider} chưa được hỗ trợ.")

    def extract_info(self, image: np.ndarray) -> dict:
        """
        Trích xuất thông tin từ ảnh CCCD.

        Args:
            image: Ảnh CCCD dạng numpy array (BGR).

        Returns:
            dict: {"full_name": ..., "dob": ..., "cccd": ..., "address": ...}
        """
        # TODO: Triển khai thực tế với PaddleOCR + regex
        # Hiện tại trả về mock để test luồng
        return {
            "full_name": "",
            "dob": "",
            "cccd": "",
            "address": "",
        }


# Singleton
ocr_service = OCRService()
