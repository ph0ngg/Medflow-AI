import cv2
import time
import numpy
import torch
import onnxruntime
from pathlib import Path

from .utils import Face
from ai_modules.face_recognizor import ArcfaceInference

# Thư mục ai_modules (nơi chứa face_detection, face_recognizor, faiss)
_AI_MODULES_DIR = Path(__file__).resolve().parent.parent


class YoloFaceInference:
    def __init__(self, model_path: str, provider = 'cuda', have_arcface_model=True):
        if provider == "cuda":
            providers = ['CUDAExecutionProvider']
        else:
            providers = ['CPUExecutionProvider']
        # Tạo inference session
        self.session = onnxruntime.InferenceSession(
            model_path,
            providers=providers
        )
        self.face_detector_size = (640, 640)
        self.detect_threshold = 0.5
        self.landmarker_threshold = 0.5
        self.nms_threshold = 0.5
        self.warmup()
        if have_arcface_model:
            arcface_path = str(_AI_MODULES_DIR / "face_recognizor" / "weight" / "recognize.onnx")
            self.arcface_model = ArcfaceInference(arcface_path, provider)
        else:
            self.arcface_model = None
        
    def warmup(self):
        print("Detector starting warmup")
        st = time.time()
        dummy_input = numpy.zeros((1, 3, * self.face_detector_size), dtype=numpy.float32)
        detection = self.session.run(None,
            {
                'input': dummy_input
            })  
        print("Detector warmup complete: ", time.time() - st)

    def resize_frame_resolution(self, vision_frame, max_resolution):
        height, width = vision_frame.shape[:2]
        max_width, max_height = max_resolution

        if height > max_height or width > max_width:
            scale = min(max_height / height, max_width / width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            return cv2.resize(vision_frame, (new_width, new_height))
        return vision_frame
    
    def prepare_detect_frame(self, temp_vision_frame):
        face_detector_width, face_detector_height = self.face_detector_size
        detect_vision_frame = numpy.zeros((face_detector_height, face_detector_width, 3))
        detect_vision_frame[:temp_vision_frame.shape[0], :temp_vision_frame.shape[1], :] = temp_vision_frame
        detect_vision_frame = (detect_vision_frame - 127.5) / 128.0
        detect_vision_frame = numpy.expand_dims(detect_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
        
        return detect_vision_frame
    
    def normalize_bounding_box(self, bounding_box):
        x1, y1, x2, y2 = bounding_box
        x1, x2 = sorted([ x1, x2 ])
        y1, y2 = sorted([ y1, y2 ])
        
        return numpy.array([ x1, y1, x2, y2 ])

    def detect_faces(self, vision_frame, threshold=None):
        if threshold is None:
            threshold = self.detect_threshold
        all_bounding_boxes = []
        all_face_scores = []
        all_face_landmarks_5 = []
        bounding_boxes = []
        face_scores = []
        face_landmarks_5 = []
        temp_vision_frame = self.resize_frame_resolution(vision_frame, self.face_detector_size)
        ratio_height = vision_frame.shape[0] / temp_vision_frame.shape[0]
        ratio_width = vision_frame.shape[1] / temp_vision_frame.shape[1]
        detect_vision_frame = self.prepare_detect_frame(temp_vision_frame)
        
        # Thực hiện inference
        detection = self.session.run(None,
		{
			'input': detect_vision_frame
		})
        
        detection = numpy.squeeze(detection).T
        bounding_box_raw, score_raw, face_landmark_5_raw = numpy.split(detection, [ 4, 5 ], axis = 1)
        keep_indices = numpy.where(score_raw > threshold)[0]
        
        if numpy.any(keep_indices):
            bounding_box_raw, face_landmark_5_raw, score_raw = bounding_box_raw[keep_indices], face_landmark_5_raw[keep_indices], score_raw[keep_indices]

            for bounding_box in bounding_box_raw:
                bounding_boxes.append(numpy.array(
                [
                    (bounding_box[0] - bounding_box[2] / 2) * ratio_width,
                    (bounding_box[1] - bounding_box[3] / 2) * ratio_height,
                    (bounding_box[0] + bounding_box[2] / 2) * ratio_width,
                    (bounding_box[1] + bounding_box[3] / 2) * ratio_height,
                ]))

            face_scores = score_raw.ravel().tolist()
            face_landmark_5_raw[:, 0::3] = (face_landmark_5_raw[:, 0::3]) * ratio_width
            face_landmark_5_raw[:, 1::3] = (face_landmark_5_raw[:, 1::3]) * ratio_height

            for face_landmark_5 in face_landmark_5_raw:
                face_landmarks_5.append(numpy.array(face_landmark_5.reshape(-1, 3)[:, :2]))
        
        all_bounding_boxes.extend(bounding_boxes)
        all_face_scores.extend(face_scores)
        all_face_landmarks_5.extend(face_landmarks_5)
        all_bounding_boxes = [self.normalize_bounding_box(all_bounding_box) for all_bounding_box in all_bounding_boxes ]
        
        return bounding_boxes, face_scores, face_landmarks_5
    
    def apply_nms(self, bounding_boxes, face_scores, score_threshold, nms_threshold):
        normed_bounding_boxes = [ (x1, y1, x2 - x1, y2 - y1) for (x1, y1, x2, y2) in bounding_boxes ]
        keep_indices = cv2.dnn.NMSBoxes(normed_bounding_boxes, face_scores, score_threshold = score_threshold, nms_threshold = nms_threshold)
        return keep_indices
    
    def create_faces(self, vision_frame, bounding_boxes, face_scores, face_landmarks_5):
        faces = []
        keep_indices = self.apply_nms(bounding_boxes, face_scores, self.detect_threshold, self.nms_threshold)

        for index in keep_indices:
            bounding_box = bounding_boxes[index]
            face_landmark_5 = face_landmarks_5[index]

            if self.arcface_model is not None:
                embedding, normed_embedding = self.arcface_model.calc_embedding(vision_frame, face_landmark_5)
            else:
                embedding, normed_embedding = None, None
            
            faces.append(Face(
                bounding_box = bounding_box,
                landmark_5 = face_landmark_5,
                embedding = embedding,
                normed_embedding = normed_embedding,
                gender = None,
                age = None,
                race = None,
                id=None,
                name=None
            ))
        return faces
    
    def get_many_faces(self, vision_frame:numpy.ndarray, threshold=0.5):
        many_faces = []
        all_bounding_boxes = []
        all_face_scores = []
        all_face_landmarks_5 = []
        bounding_boxes, face_scores, face_landmarks_5 = self.detect_faces(vision_frame, threshold=threshold)
        all_bounding_boxes.extend(bounding_boxes)
        all_face_scores.extend(face_scores)
        all_face_landmarks_5.extend(face_landmarks_5)

        if all_bounding_boxes and all_face_scores and all_face_landmarks_5:
            faces = self.create_faces(vision_frame, all_bounding_boxes, all_face_scores, all_face_landmarks_5)

            if faces:
                many_faces.extend(faces)
                        
        return many_faces