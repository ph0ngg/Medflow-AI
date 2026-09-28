"""
Service nhận diện & xác thực khuôn mặt.
Dùng model từ ai_modules (Face_Detection + ArcFace + FAISS).
"""
from pathlib import Path

import numpy as np

from config import FACE_DETECTION_MODEL
from ai_modules.face_detection import YoloFaceInference
from ai_modules.faiss import FaissService


class FaceService:
    """
    Quản lý toàn bộ pipeline nhận diện khuôn mặt:
    1. Phát hiện khuôn mặt (YOLOv8)
    2. Trích xuất embedding (ArcFace)
    3. So khớp với database (FAISS)
    """

    def __init__(self):
        self._detector = None
        self._faiss = None

    @property
    def detector(self):
        if self._detector is None:
            self._detector = YoloFaceInference(FACE_DETECTION_MODEL)
        return self._detector

    @property
    def faiss(self):
        if self._faiss is None:
            self._faiss = FaissService()
        return self._faiss

    def detect_faces(self, frame: np.ndarray):
        """Phát hiện tất cả khuôn mặt trong frame."""
        return self.detector.get_many_faces(frame)

    def identify_face(self, face) -> tuple:
        """
        Nhận diện một khuôn mặt.
        Returns: (id, name) hoặc ("", "") nếu không khớp.
        """
        if face.normed_embedding is not None:
            return self.faiss.search(face.normed_embedding, k=1)
        return "", ""

    def register_face(self, image: np.ndarray, name: str) -> bool:
        """
        Đăng ký khuôn mặt mới vào FAISS.
        """
        faces = self.detect_faces(image)
        if not faces:
            return False

        # Lấy ID mới
        import json
        id2name_path = Path(__file__).resolve().parent.parent / "ai_modules" / "faiss" / "id2name.json"
        with open(id2name_path, "r") as f:
            data = json.load(f)
        ids = list(map(int, data.keys()))
        new_id = max(ids) + 1 if ids else 1

        self.faiss.add(new_id, faces[0].normed_embedding, name)
        return True


# Singleton
face_service = FaceService()
