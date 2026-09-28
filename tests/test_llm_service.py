"""
Test LLM service — đảm bảo giọng "nhân viên tiếp đón", không tư vấn y khoa (PRD mục 9).
"""
from app.services.llm_service import llm_service


def test_sanitize_blocks_medical_advice():
    bad = (
        "Bạn có thể đang gặp phải một số vấn đề về tiêu hóa. "
        "Nếu đau bụng kéo dài, bạn nên đến khám bác sĩ để được tư vấn và điều trị phù hợp."
    )
    out = llm_service._sanitize_response(bad)
    assert "khám bác sĩ" not in out
    assert "điều trị" not in out
    assert "khoa khám" in out  # câu tiếp đón an toàn


def test_sanitize_keeps_short_reception_response():
    good = "Anh/chị đau bụng bao lâu rồi? Có kèm buồn nôn hoặc sốt không?"
    assert llm_service._sanitize_response(good) == good


def test_sanitize_blocks_long_response():
    long_text = "chi tiết " * 60
    out = llm_service._sanitize_response(long_text)
    assert out != long_text
