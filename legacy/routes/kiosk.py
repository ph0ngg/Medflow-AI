"""
API Routes cho Kiosk MedFlow AI.
Các endpoint chính cho frontend kiosk gọi.
"""
import io
import json
import os

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from orchestrator import orchestrator, SessionState

# Services được import lazy (chỉ load khi cần, tránh lỗi thiếu CV2/ONNX)
# from services.face_service import face_service
# from services.stt_service import stt_service
# from services.tts_service import tts_service
# from services.ocr_service import ocr_service

router = APIRouter(prefix="/api/kiosk", tags=["kiosk"])


# ── Request/Response Models ────────────────────────────

class MessageRequest(BaseModel):
    session_id: str
    message: str


class ConfirmRequest(BaseModel):
    session_id: str


# ── Lazy imports (tránh lỗi khi chưa cài CV2/ONNX) ──

def _get_face_service():
    from services.face_service import face_service
    return face_service

def _get_stt_service():
    from services.stt_service import stt_service
    return stt_service

def _get_tts_service():
    from services.tts_service import tts_service
    return tts_service

def _get_ocr_service():
    from services.ocr_service import ocr_service
    return ocr_service


# ── 1. Phát hiện khuôn mặt từ frame ────────────────────

@router.post("/detect-face")
async def detect_face(image: UploadFile = File(...)):
    """
    Nhận ảnh từ camera, phát hiện và nhận diện khuôn mặt.
    Gọi liên tục từ frontend khi chưa có session.
    """
    import numpy as np
    import cv2

    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    result = orchestrator.process_frame(frame)
    return JSONResponse(result)


# ── 2. Bắt đầu phiên ───────────────────────────────────

@router.post("/start-session")
async def start_session(face_name: str = Form(None), face_id: str = Form(None)):
    """
    Bắt đầu phiên giao dịch mới.
    - Nếu nhận diện được → bệnh nhân cũ
    - Nếu không → bệnh nhân mới
    """
    session = orchestrator.start_session(face_name, face_id)

    # Nếu là bệnh nhân cũ, lấy context để chào hỏi
    if session.is_returning:
        context = orchestrator.get_patient_context(session)
        greeting = f"Xin chào {session.patient_name or 'anh/chị'}! Anh/chị đến khám theo lịch hẹn hay muốn đăng ký khám triệu chứng mới?"
        return JSONResponse({
            **session.to_dict(),
            "greeting": greeting,
            "context": context,
        })
    else:
        return JSONResponse({
            **session.to_dict(),
            "message": "Chào mừng anh/chị! Hệ thống sẽ hỗ trợ xác thực danh tính. Anh/chị vui lòng nhìn vào camera hoặc quét CCCD.",
        })


# ── 3. Gửi tin nhắn hội thoại ──────────────────────────

@router.post("/message")
async def send_message(req: MessageRequest):
    """
    Gửi message text từ bệnh nhân đến AI.
    """
    result = orchestrator.process_message(req.session_id, req.message)
    return JSONResponse(result)


# ── 4. Gửi giọng nói (STT → Text → LLM) ────────────────

@router.post("/voice-message")
async def voice_message(session_id: str = Form(...), audio: UploadFile = File(...)):
    """
    Nhận file audio, chuyển thành text, sau đó xử lý qua LLM.
    """
    import subprocess
    import tempfile

    # Lưu file audio tạm (giữ nguyên định dạng từ browser)
    suffix = ".webm" if "webm" in (audio.content_type or "") else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(await audio.read())
        raw_path = f.name

    # Convert về WAV 16kHz mono (PhoWhisper yêu cầu)
    wav_path = raw_path + ".wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", raw_path, "-ar", "16000", "-ac", "1", wav_path],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        # ffmpeg không có sẵn → thử dùng trực tiếp file gốc
        import shutil
        shutil.copy(raw_path, wav_path)
    finally:
        os.remove(raw_path)

    # STT
    try:
        stt_service = _get_stt_service()
        text = stt_service.transcribe(wav_path)
    except Exception as e:
        return JSONResponse(
            {"error": f"STT failed: {str(e)}"}, status_code=500
        )
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

    if not text:
        return JSONResponse({"error": "Không nhận diện được giọng nói"}, status_code=400)

    # Xử lý qua orchestrator
    result = orchestrator.process_message(session_id, text)
    result["transcribed_text"] = text
    return JSONResponse(result)


# ── 5. Tổng hợp giọng nói (TTS) ─────────────────────────

@router.post("/tts")
async def text_to_speech(req: MessageRequest):
    """
    Chuyển text → giọng nói.
    """
    try:
        tts_service = _get_tts_service()
        audio_bytes = tts_service.synthesize(req.message)
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


# ── 6. Xác nhận & cấp số ───────────────────────────────

@router.post("/confirm")
async def confirm_ticket(req: ConfirmRequest):
    """
    Bệnh nhân xác nhận đăng ký → cấp số thứ tự.
    """
    result = orchestrator.confirm_and_issue(req.session_id)
    return JSONResponse(result)


# ── 7. Kết thúc phiên ──────────────────────────────────

@router.post("/end-session")
async def end_session(req: ConfirmRequest):
    """
    Kết thúc phiên giao dịch.
    """
    orchestrator.end_session(req.session_id)
    return JSONResponse({"message": "Session ended"})


# ── 8. Trạng thái session ──────────────────────────────

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Lấy trạng thái hiện tại của session.
    """
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return JSONResponse(session.to_dict())


# ── 9. Quét CCCD ───────────────────────────────────────

@router.post("/scan-cccd")
async def scan_cccd(image: UploadFile = File(...)):
    """
    Quét CCCD, trích xuất thông tin.
    """
    import numpy as np
    import cv2

    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    ocr_service = _get_ocr_service()
    info = ocr_service.extract_info(img)
    return JSONResponse(info)


# ── 10. Đăng ký khuôn mặt mới ──────────────────────────

@router.post("/register-face")
async def register_face(name: str = Form(...), image: UploadFile = File(...)):
    """
    Đăng ký khuôn mặt mới vào hệ thống.
    """
    import numpy as np
    import cv2

    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    face_service = _get_face_service()
    success = face_service.register_face(img, name)
    if success:
        return JSONResponse({"message": f"Đã đăng ký khuôn mặt cho {name}"})
    else:
        raise HTTPException(status_code=400, detail="Không tìm thấy khuôn mặt trong ảnh")
