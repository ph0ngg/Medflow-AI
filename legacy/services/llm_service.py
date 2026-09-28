"""
Service LLM - Xử lý hội thoại & phân tích ý định.
Dùng GPT-4o (hoặc Gemini) để:
- Nhận diện intent của bệnh nhân
- Trích xuất triệu chứng
- Hỏi thêm nếu thiếu thông tin
- Đưa ra phản hồi tự nhiên
"""
import json
from config import LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, GOOGLE_API_KEY, COHERE_API_KEY


# ── Prompt hệ thống ─────────────────────────────────────
SYSTEM_PROMPT = """Bạn là trợ lý AI tại kiosk tiếp đón bệnh viện MedFlow.
Nhiệm vụ của bạn:
1. Xác định intent của bệnh nhân: check_in (check-in lịch hẹn), new_visit (khám triệu chứng mới), follow_up (khám lại)
2. Nếu bệnh nhân mô tả triệu chứng, hãy hỏi thêm 1-2 câu ngắn để làm rõ (sốt?, mức độ đau?, bao lâu?)
3. KHÔNG chẩn đoán bệnh. Chỉ ghi nhận triệu chứng và đề xuất khoa khám.
4. Nếu có dấu hiệu khẩn cấp (đau ngực dữ dội, khó thở nặng, bất tỉnh...), hãy hướng dẫn bệnh nhân gặp nhân viên y tế NGAY.

Trả lời dưới dạng JSON:
{
    "intent": "check_in" | "new_visit" | "follow_up" | "emergency",
    "symptoms": ["triệu chứng 1", "triệu chứng 2"],
    "response": "Câu trả lời bằng tiếng Việt cho bệnh nhân",
    "need_more_info": true | false,
    "suggested_department": "Tên khoa" | null
}"""


class LLMService:
    """
    Xử lý hội thoại AI. Giao tiếp với OpenAI / Gemini API.
    """

    def __init__(self):
        self.provider = LLM_PROVIDER
        self.model = LLM_MODEL
        self.conversations = {}  # Lưu context hội thoại theo session_id

    def chat(self, session_id: str, user_message: str, patient_context: dict = None) -> dict:
        """
        Gửi message của bệnh nhân đến LLM, nhận về JSON phản hồi.

        Args:
            session_id: ID phiên hội thoại
            user_message: Câu nói của bệnh nhân
            patient_context: dict chứa thông tin bệnh nhân (tên, lịch sử, lịch hẹn...)

        Returns:
            dict JSON phản hồi từ LLM.
        """
        # Khởi tạo hoặc lấy lịch sử hội thoại
        if session_id not in self.conversations:
            self.conversations[session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
            # Thêm context bệnh nhân nếu có
            if patient_context:
                ctx = f"Thông tin bệnh nhân: {json.dumps(patient_context, ensure_ascii=False)}"
                self.conversations[session_id].append({"role": "system", "content": ctx})

        self.conversations[session_id].append({"role": "user", "content": user_message})

        if self.provider == "openai":
            result = self._chat_openai(session_id)
        elif self.provider == "gemini":
            result = self._chat_gemini(session_id)
        elif self.provider == "cohere":
            result = self._chat_cohere(session_id)
        else:
            result = self._mock_response(user_message)

        self.conversations[session_id].append({"role": "assistant", "content": json.dumps(result, ensure_ascii=False)})
        return result

    def _chat_openai(self, session_id: str) -> dict:
        """Gọi OpenAI API."""
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model=self.model,
            messages=self.conversations[session_id],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)

    def _chat_gemini(self, session_id: str) -> dict:
        """Gọi Google Gemini API."""
        # TODO: Implement
        return self._mock_response("")

    def _chat_cohere(self, session_id: str) -> dict:
        """Gọi Cohere API (free tier, model command-r-plus)."""
        import cohere

        client = cohere.ClientV2(api_key=COHERE_API_KEY)

        # Cohere V2 đã hỗ trợ role "system" trực tiếp trong messages
        response = client.chat(
            model=self.model,
            messages=self.conversations[session_id],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        # Parse JSON từ response
        raw = response.text if hasattr(response, "text") else response.message.content[0].text

        # Loại bỏ markdown code block nếu có
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Cohere response is not valid JSON: {raw[:300]}")

    def _mock_response(self, user_message: str) -> dict:
        """
        Phản hồi mẫu khi chưa có API key.
        Đây là mock để test luồng tổng thể.
        """
        msg = user_message.lower()
        if any(kw in msg for kw in ["đau ngực", "khó thở", "bất tỉnh"]):
            return {
                "intent": "emergency",
                "symptoms": [],
                "response": "Các triệu chứng anh/chị cung cấp có thể cần được nhân viên y tế đánh giá ngay. Vui lòng liên hệ nhân viên y tế gần nhất.",
                "need_more_info": False,
                "suggested_department": None,
            }
        elif any(kw in msg for kw in ["lịch hẹn", "check-in", "check in"]):
            return {
                "intent": "check_in",
                "symptoms": [],
                "response": "Hệ thống đang kiểm tra lịch hẹn của anh/chị...",
                "need_more_info": False,
                "suggested_department": None,
            }
        elif any(kw in msg for kw in ["khám lại", "tái khám"]):
            return {
                "intent": "follow_up",
                "symptoms": [],
                "response": "Hệ thống sẽ tra cứu lịch sử khám của anh/chị.",
                "need_more_info": False,
                "suggested_department": None,
            }
        elif any(kw in msg for kw in ["đau bụng", "buồn nôn", "đau đầu", "ho", "sốt"]):
            return {
                "intent": "new_visit",
                "symptoms": [msg],
                "response": "Anh/chị có bị sốt không? Mức độ đau hiện tại như thế nào?",
                "need_more_info": True,
                "suggested_department": None,
            }
        else:
            return {
                "intent": "new_visit",
                "symptoms": [msg],
                "response": "Anh/chị vui lòng mô tả thêm về triệu chứng của mình để tôi có thể hỗ trợ tốt hơn.",
                "need_more_info": True,
                "suggested_department": None,
            }

    def reset_session(self, session_id: str):
        """Xóa lịch sử hội thoại của session."""
        self.conversations.pop(session_id, None)


# Singleton
llm_service = LLMService()
