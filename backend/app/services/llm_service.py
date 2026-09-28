"""
LLM Service — xử lý hội thoại, nhận diện ý định, trích xuất triệu chứng.

Nguyên tắc (PRD mục 9):
- LLM chỉ hỗ trợ khai thác thông tin & đề xuất hướng khám, KHÔNG chẩn đoán.
- Đề xuất khoa cuối cùng phải kết hợp với rule engine (xem triage_service).
- Không log PII không cần thiết.
"""
import json
import re

from app.config import (
    LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, GOOGLE_API_KEY, COHERE_API_KEY,
)
from app.rules import detect_intent_by_rules, check_emergency, DEPARTMENT_MAPPING

_DEPARTMENT_NAMES = ", ".join(DEPARTMENT_MAPPING.keys())

# Mẫu câu tư vấn y khoa mà LLM không được dùng → thay bằng câu tiếp đón an toàn
_MEDICAL_ADVICE_PATTERNS = [
    "khám bác sĩ", "đi khám bác sĩ", "gặp bác sĩ", "điều trị", "chẩn đoán",
    "uống thuốc", "dùng thuốc", "kê đơn", "bệnh lý", "có thể bạn đang",
    "bạn nên đến", "nên đến bệnh viện", "tình trạng bệnh", "tư vấn và điều trị",
]
_SAFE_RESPONSE = (
    "Anh/chị vui lòng mô tả thêm triệu chứng "
    "(đau ở đâu, kéo dài bao lâu, có sốt không) để tôi hỗ trợ đăng ký đúng khoa khám."
)

_SYSTEM_PROMPT_TEMPLATE = """Bạn là NHÂN VIÊN TIẾP ĐÓN tại quầy kiosk của bệnh viện MedFlow. Bạn KHÔNG phải bác sĩ và KHÔNG được tư vấn y khoa.

Danh sách khoa của bệnh viện: __DEPARTMENTS__.

Nhiệm vụ của bạn:
1. Xác định ý định: check_in | new_visit | follow_up | payment | lookup | support | emergency.
2. Ghi nhận triệu chứng người bệnh mô tả thành danh sách ngắn (chỉ ghi triệu chứng, không diễn giải bệnh).
3. Nếu còn thiếu thông tin để phân luồng, hỏi thêm 1-2 câu ngắn, lịch sự.
4. Nếu đã rõ triệu chứng, đề xuất MỘT khoa phù hợp từ danh sách trên vào trường suggested_department.
5. KHÔNG chẩn đoán bệnh. KHÔNG giải thích bệnh lý. KHÔNG nói "nên đi khám bác sĩ", "cần điều trị", "có thể bạn đang bị...". KHÔNG đưa lời khuyên y khoa.
6. Nếu có dấu hiệu nguy hiểm (đau ngực dữ dội, khó thở nặng, bất tỉnh...), đặt intent=emergency.

CHỈ trả về json (JSON), không thêm văn bản khác:
{
  "intent": "check_in | new_visit | follow_up | payment | lookup | support | emergency",
  "symptoms": ["triệu chứng 1", "triệu chứng 2"],
  "response": "Câu ngắn bằng tiếng Việt, giọng tiếp đón: hỏi thêm hoặc xác nhận",
  "need_more_info": true | false,
  "suggested_department": "Tên khoa" | null
}

Ví dụ người bệnh nói "tôi bị đau bụng":
{
  "intent": "new_visit",
  "symptoms": ["đau bụng"],
  "response": "Anh/chị đau bụng bao lâu rồi? Có kèm buồn nôn hoặc sốt không?",
  "need_more_info": true,
  "suggested_department": null
}"""

SYSTEM_PROMPT = _SYSTEM_PROMPT_TEMPLATE.replace("__DEPARTMENTS__", _DEPARTMENT_NAMES)


class LLMService:
    def __init__(self):
        self.provider = LLM_PROVIDER
        self.model = LLM_MODEL
        self.conversations: dict[str, list[dict]] = {}

    # ── Public API ─────────────────────────────────────
    def chat(self, session_id: str, user_message: str, patient_context: dict | None = None) -> dict:
        """Gửi message → nhận structured dict (intent, symptoms, response...)."""
        if session_id not in self.conversations:
            self.conversations[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
            if patient_context:
                ctx = json.dumps(patient_context, ensure_ascii=False)
                self.conversations[session_id].append(
                    {"role": "system", "content": f"Thông tin ngữ cảnh bệnh nhân: {ctx}"}
                )

        self.conversations[session_id].append({"role": "user", "content": user_message})

        try:
            if self.provider == "openai":
                result = self._chat_openai(session_id)
            elif self.provider == "cohere":
                result = self._chat_cohere(session_id)
            elif self.provider == "gemini":
                result = self._chat_gemini(session_id)
            else:
                result = self._mock_response(user_message)
        except Exception as e:
            # Fallback an toàn: dùng mock khi LLM lỗi (và in lỗi để dễ chẩn đoán)
            print(f"[LLM] Lỗi khi gọi provider '{self.provider}' (model '{self.model}'): {e}")
            result = self._mock_response(user_message)

        result.setdefault("intent", "new_visit")
        result.setdefault("symptoms", [])
        result.setdefault("response", "")
        result.setdefault("need_more_info", True)
        result.setdefault("suggested_department", None)

        # Chặn câu trả lời mang tính tư vấn y khoa (PRD mục 9)
        result["response"] = self._sanitize_response(result.get("response", ""))

        self.conversations[session_id].append(
            {"role": "assistant", "content": json.dumps(result, ensure_ascii=False)}
        )
        return result

    def reset_session(self, session_id: str):
        self.conversations.pop(session_id, None)

    # ── Providers ───────────────────────────────────────
    def _chat_openai(self, session_id: str) -> dict:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=self.model,
            messages=self.conversations[session_id],
            response_format={"type": "json_object"},
            #temperature=0.3,
        )
        return self._parse_json(response.choices[0].message.content)

    def _chat_cohere(self, session_id: str) -> dict:
        import cohere
        client = cohere.ClientV2(api_key=COHERE_API_KEY)
        response = client.chat(
            model=self.model,
            messages=self.conversations[session_id],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        raw = response.text if hasattr(response, "text") else response.message.content[0].text
        return self._parse_json(raw)

    def _chat_gemini(self, session_id: str) -> dict:
        # TODO: implement khi cần
        return self._mock_response("")

    @staticmethod
    def _parse_json(raw: str) -> dict:
        raw = (raw or "").strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[:-3]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"LLM response is not valid JSON: {raw[:300]}")

    @staticmethod
    def _sanitize_response(text: str) -> str:
        """Chặn câu trả lời tư vấn y khoa, đảm bảo giọng tiếp đón."""
        text = (text or "").strip()
        lowered = text.lower()
        if any(p in lowered for p in _MEDICAL_ADVICE_PATTERNS):
            return _SAFE_RESPONSE
        if len(text) > 180:
            return _SAFE_RESPONSE
        return text

    # ── Mock (offline, deterministic cho test/demo) ─────
    def _mock_response(self, user_message: str) -> dict:
        msg = (user_message or "").lower().strip()

        if check_emergency(msg):
            return {
                "intent": "emergency",
                "symptoms": [],
                "response": "Các triệu chứng anh/chị cung cấp có thể cần được nhân viên y tế đánh giá ngay. Vui lòng liên hệ nhân viên y tế gần nhất.",
                "need_more_info": False,
                "suggested_department": None,
            }

        intent = detect_intent_by_rules(msg) or "new_visit"

        # Lấy các từ khóa triệu chứng khớp để làm "symptoms"
        from app.rules import DEPARTMENT_MAPPING
        all_keywords = [kw for kws in DEPARTMENT_MAPPING.values() for kw in kws]
        symptoms = [kw for kw in all_keywords if kw in msg]

        if intent == "check_in":
            return {
                "intent": intent,
                "symptoms": symptoms,
                "response": "Hệ thống đang kiểm tra lịch hẹn của anh/chị...",
                "need_more_info": False,
                "suggested_department": None,
            }
        if intent == "follow_up":
            return {
                "intent": intent,
                "symptoms": symptoms,
                "response": "Hệ thống sẽ tra cứu lịch sử khám gần nhất của anh/chị.",
                "need_more_info": False,
                "suggested_department": None,
            }
        if intent in ("payment", "lookup", "support"):
            return {
                "intent": intent,
                "symptoms": symptoms,
                "response": "Tôi sẽ hỗ trợ anh/chị ngay sau đây.",
                "need_more_info": False,
                "suggested_department": None,
            }

        # new_visit
        if not symptoms:
            return {
                "intent": "new_visit",
                "symptoms": [msg] if msg else [],
                "response": "Anh/chị vui lòng mô tả thêm triệu chứng để tôi hỗ trợ chính xác hơn.",
                "need_more_info": True,
                "suggested_department": None,
            }

        # Có triệu chứng → mock đề xuất khoa luôn (giống LLM thật quyết định)
        from app.rules import suggest_department_by_rules
        rule_suggestion = suggest_department_by_rules(msg)
        return {
            "intent": "new_visit",
            "symptoms": symptoms,
            "response": "Tôi đã ghi nhận triệu chứng của anh/chị.",
            "need_more_info": False,
            "suggested_department": rule_suggestion.department if rule_suggestion else None,
        }


llm_service = LLMService()
