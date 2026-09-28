"""
API Routes — Kiosk (MedFlow AI).

Endpoint chính cho frontend kiosk. Thiết kế theo API_SPEC.
"""
import io
import os

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.orchestrator import orchestrator
from app.services.triage_service import triage_service

router = APIRouter(prefix="/api/kiosk", tags=["kiosk"])


class MessageRequest(BaseModel):
    session_id: str
    message: str


class SessionRequest(BaseModel):
    session_id: str


# ── 1. Phát hiện & nhận diện khuôn mặt ─────────────────
@router.post("/detect-face")
async def detect_face(image: UploadFile = File(...)):
    import numpy as np
    import cv2

    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return JSONResponse({"detected": False, "error": "invalid_image"}, status_code=400)
    return JSONResponse(orchestrator.process_frame(frame))


# ── 2. Bắt đầu phiên ───────────────────────────────────
@router.post("/start-session")
async def start_session(face_name: str = Form(None), face_id: str = Form(None)):
    session = orchestrator.start_session(face_name, face_id)
    if session.is_returning:
        context = orchestrator.get_profile(session)
        return JSONResponse({
            **session.to_dict(),
            "greeting": (
                f"Xin chào {session.patient_name or 'anh/chị'}! "
                f"Anh/chị đến khám theo lịch hẹn, tái khám hay có triệu chứng mới?"
            ),
            **context,
        })
    return JSONResponse({
        **session.to_dict(),
        "message": "Chào mừng anh/chị! Vui lòng quét CCCD hoặc nhập mã bệnh nhân để xác thực danh tính.",
    })


# ── 3. Quét CCCD (OCR) ─────────────────────────────────
@router.post("/scan-cccd")
async def scan_cccd(image: UploadFile = File(...)):
    import numpy as np
    import cv2

    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return JSONResponse({"error": "invalid_image"}, status_code=400)

    from app.services.ocr_service import ocr_service
    info = ocr_service.extract_info(img)
    return JSONResponse({"info": info})


# ── 4. Xác thực qua CCCD / mã bệnh nhân ────────────────
@router.post("/verify-cccd")
async def verify_cccd(session_id: str = Form(...), cccd: str = Form(None), code: str = Form(None)):
    if code:
        # Mã bệnh nhân (dự phòng) → tra HIS trực tiếp
        from app.adapters import get_his_adapter
        from app.session import SessionState
        session = orchestrator.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        record = get_his_adapter().get_patient_by_code(code)
        if not record.found:
            return JSONResponse({"error": "patient_not_found", "response": "Không tìm thấy mã bệnh nhân này."})
        session.patient_id = record.patient_id
        session.patient_name = record.full_name
        session.is_returning = record.is_returning
        session.identity_method = "code"
        session.state = SessionState.PROFILE_REVIEW
        return JSONResponse({**session.to_dict(), **orchestrator.get_profile(session)})

    result = orchestrator.verify_cccd(session_id, cccd or "")
    return JSONResponse(result)


# ── 4b. Đăng ký bệnh nhân mới ──────────────────────────
@router.post("/register")
async def register_patient(
    full_name: str = Form(None),
    dob: str = Form(None),
    address: str = Form(""),
    phone: str = Form(""),
    cccd: str = Form(None),
    bhyt_code: str = Form(None),
    face_image: UploadFile = File(None),
):
    """
    Đăng ký bệnh nhân mới từ form kiosk.
    Bắt buộc: họ tên, ngày sinh, (CCCD hoặc BHYT).
    `face_image` (tùy chọn): đăng ký khuôn mặt.
    """
    import numpy as np
    import cv2

    face_arr = None
    if face_image is not None:
        contents = await face_image.read()
        nparr = np.frombuffer(contents, np.uint8)
        face_arr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    result = orchestrator.register_patient(
        full_name or "", dob or "", address, phone, cccd, bhyt_code, face_arr
    )
    return JSONResponse(result)


# ── 5. Trạng thái session ──────────────────────────────
@router.get("/session/{session_id}")
async def get_session(session_id: str):
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return JSONResponse(session.to_dict())


# ── 6. Hội thoại (text) ────────────────────────────────
@router.post("/message")
async def send_message(req: MessageRequest):
    result = orchestrator.process_message(req.session_id, req.message)
    return JSONResponse(result)


# ── 7. Giọng nói (STT → LLM) ───────────────────────────
@router.post("/voice-message")
async def voice_message(session_id: str = Form(...), audio: UploadFile = File(...)):
    import shutil
    import subprocess
    import tempfile

    suffix = ".webm" if "webm" in (audio.content_type or "") else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(await audio.read())
        raw_path = f.name

    wav_path = raw_path + ".wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", raw_path, "-ar", "16000", "-ac", "1", wav_path],
            capture_output=True, check=True,
        )
    except Exception:
        shutil.copy(raw_path, wav_path)
    finally:
        if os.path.exists(raw_path):
            os.remove(raw_path)

    try:
        from app.services.stt_service import stt_service
        text = stt_service.transcribe(wav_path)
    except Exception as e:
        return JSONResponse({"error": f"STT failed: {str(e)}"}, status_code=500)
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

    if not text:
        return JSONResponse({"error": "Không nhận diện được giọng nói"}, status_code=400)

    result = orchestrator.process_message(session_id, text)
    result["transcribed_text"] = text
    return JSONResponse(result)


# ── 8. TTS ─────────────────────────────────────────────
@router.post("/tts")
async def text_to_speech(req: MessageRequest):
    try:
        from app.services.tts_service import tts_service
        audio_bytes = tts_service.synthesize(req.message)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


# ── 9. Chọn khoa (fallback touch) ──────────────────────
@router.post("/select-department")
async def select_department(session_id: str = Form(...), department: str = Form(...)):
    return JSONResponse(orchestrator.select_department(session_id, department))


# ── 10. Thanh toán ─────────────────────────────────────
@router.post("/pay")
async def pay(session_id: str = Form(...), method: str = Form("mock")):
    return JSONResponse(orchestrator.process_payment(session_id, method))


# ── 11. Xác nhận & cấp số ──────────────────────────────
@router.post("/confirm")
async def confirm_ticket(req: SessionRequest):
    return JSONResponse(orchestrator.confirm_and_issue(req.session_id))


# ── 12. Kết thúc phiên ─────────────────────────────────
@router.post("/end-session")
async def end_session(req: SessionRequest):
    orchestrator.end_session(req.session_id)
    return JSONResponse({"message": "Session ended"})


# ── 13. Danh sách khoa / hàng đợi ──────────────────────
@router.get("/departments")
async def list_departments():
    return JSONResponse(triage_service.list_departments())


@router.get("/queue/{department}")
async def get_queue(department: str):
    return JSONResponse(triage_service.get_queue_info(department))
