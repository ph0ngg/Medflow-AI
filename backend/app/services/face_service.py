"""
Face Service — phát hiện & nhận diện khuôn mặt.

Tái sử dụng ai_modules (YOLOv8 face detection + ArcFace + FAISS).
Nếu model/ONNX runtime chưa cài → tự degrade (không phát hiện được),
kiosk vẫn chạy với phương thức dự phòng (CCCD/QR/mã bệnh nhân).
"""
import json
from pathlib import Path
from typing import Optional

import numpy as np

from app.config import (
    FACE_DETECTION_MODEL, FAISS_ID2NAME_PATH, AI_MODULES_DIR,
)


class FaceService:
    def __init__(self):
        self._detector = None
        self._faiss = None
        self._init_error: str | None = None

    def _ensure(self):
        if self._detector is not None or self._init_error is not None:
            return
        try:
            from ai_modules.face_detection import YoloFaceInference
            from ai_modules.faiss import FaissService
            self._detector = YoloFaceInference(FACE_DETECTION_MODEL)
            self._faiss = FaissService()
        except Exception as e:  # noqa: BLE001 — degrade gracefully
            self._init_error = str(e)

    @property
    def available(self) -> bool:
        self._ensure()
        return self._init_error is None

    @property
    def init_error(self) -> str | None:
        self._ensure()
        return self._init_error

    def detect_faces(self, frame: np.ndarray):
        self._ensure()
        if self._init_error is not None:
            return []
        try:
            return self._detector.get_many_faces(frame)
        except Exception:
            return []

    def identify_face(self, face) -> tuple:
        """Returns (id, name) hoặc ("", "") nếu không khớp."""
        embedding = getattr(face, "normed_embedding", None)
        if embedding is not None and self._faiss is not None:
            try:
                return self._faiss.search(embedding, k=1)
            except Exception:
                return "", ""
        return "", ""

    def register_face(self, image: np.ndarray, name: str) -> Optional[int]:
        """Đăng ký khuôn mặt vào FAISS → trả về id (None nếu thất bại/không có mặt)."""
        self._ensure()
        if self._init_error is not None:
            return None
        faces = self.detect_faces(image)
        if not faces:
            return None

        try:
            with open(FAISS_ID2NAME_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        ids = [int(k) for k in data.keys() if str(k).isdigit()]
        new_id = max(ids) + 1 if ids else 1

        if self._faiss.add(new_id, faces[0].normed_embedding, name):
            return new_id
        return None


face_service = FaceService()
