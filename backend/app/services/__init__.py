"""
Services — MedFlow AI.
Chỉ import service nhẹ khi khởi tạo; các service nặng (CV2/ONNX) được
import lazy trong từng module để backend khởi động được khi thiếu model.
"""
from app.services.llm_service import llm_service, LLMService
from app.services.triage_service import triage_service, TriageService

__all__ = ["llm_service", "LLMService", "triage_service", "TriageService"]
