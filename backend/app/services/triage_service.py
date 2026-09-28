"""
Triage Service — phân luồng (kết hợp LLM + rules + adapters).

Nguyên tắc (PRD mục 9):
- KHÔNG chẩn đoán, chỉ đề xuất hướng khám.
- Đề xuất khoa = LLM suggestion + rule engine + dữ liệu khoa hợp lệ.
- Red flag luôn được kiểm tra bằng rule trước khi cấp số.
"""
from typing import Optional

from app.rules import (
    check_emergency,
    suggest_department_by_rules,
    DepartmentSuggestion,
    REGISTRATION_FEE,
    INSURANCE_COVERAGE_PERCENT,
)
from app.adapters import get_queue_adapter, get_payment_adapter


class TriageService:
    def check_emergency(self, text: str) -> bool:
        return check_emergency(text)

    def suggest_department(
        self,
        symptoms: list[str],
        llm_department: Optional[str] = None,
        valid_departments: Optional[list[str]] = None,
    ) -> Optional[DepartmentSuggestion]:
        """
        Đề xuất khoa — LLM quyết định chính, rule chỉ là fallback.

        1. Nếu LLM đưa ra khoa (khớp mềm với danh sách khoa hợp lệ) → dùng LLM.
        2. Ngược lại → rule-based keyword matching.
        """
        valid = valid_departments or []

        # 1) Ưu tiên LLM (khớp mềm tên khoa)
        if llm_department:
            matched = self._match_department(llm_department, valid)
            if matched:
                return DepartmentSuggestion(
                    department=matched,
                    reason="AI đề xuất dựa trên mô tả triệu chứng",
                    source="llm",
                    confidence=0.85,
                )

        # 2) Fallback rule-based (khi LLM không đưa ra khoa hợp lệ)
        rule_result = suggest_department_by_rules(" ".join(symptoms or []))
        if rule_result:
            return rule_result

        return None

    @staticmethod
    def _match_department(llm_name: str, valid: list[str]) -> Optional[str]:
        """Khớp mềm tên khoa LLM đưa ra với danh sách khoa hợp lệ.

        Chịu được viết hoa/thường, không dấu, hoặc kèm tiền tố "Khoa ...".
        """
        from app.rules import normalize
        target = normalize(llm_name)
        if not target:
            return None
        for name in valid:
            if normalize(name) == target:
                return name
        for name in valid:
            n = normalize(name)
            if n and (n in target or target in n):
                return name
        return None

    def get_queue_info(self, department: str) -> dict:
        return get_queue_adapter().get_queue_info(department).__dict__

    def issue_ticket(self, patient_id: int, department: str) -> dict:
        return get_queue_adapter().issue_ticket(patient_id, department)

    def list_departments(self) -> list[dict]:
        return get_queue_adapter().list_departments()

    def estimate_payment(self, patient_id: int, insurance_covered: bool) -> dict:
        """Tính toán phí (prototype) và tạo payment pending nếu cần."""
        amount = float(REGISTRATION_FEE)
        covered = (amount * INSURANCE_COVERAGE_PERCENT / 100) if insurance_covered else 0.0
        payment = get_payment_adapter().create_payment(patient_id, amount, covered)
        return payment.__dict__


triage_service = TriageService()
