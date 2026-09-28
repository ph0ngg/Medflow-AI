# Services được import lazy để tránh lỗi thiếu dependencies (CV2, numpy, onnxruntime)
# Sử dụng _get_xxx_service() hoặc import trực tiếp từng file khi cần.

# Chỉ import các service nhẹ (không phụ thuộc CV2/ONNX)
from .llm_service import llm_service, LLMService
from .triage_service import triage_service, TriageService

# Các service nặng - import lazy khi cần
# from .face_service import face_service, FaceService
# from .stt_service import stt_service, STTService
# from .tts_service import tts_service, TTSService
# from .ocr_service import ocr_service, OCRService
