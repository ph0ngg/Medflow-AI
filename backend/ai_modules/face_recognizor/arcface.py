import time
import numpy
import onnxruntime
from .utils import warp_face_by_face_landmark_5

class ArcfaceInference:
    def __init__(self, model_path: str, provider = 'cuda'):
        if provider == "cuda":
            providers = ['CUDAExecutionProvider']
        else:
            providers = ['CPUExecutionProvider']
        # Tạo inference session
        self.session = onnxruntime.InferenceSession(
            model_path,
            providers=providers
        )
        self.size = (112, 112)
        self.template = "arcface_112_v2"
        self.warmup()
        
    def warmup(self):
        print("Arcface starting warmup")
        st = time.time()
        dummy_input = numpy.zeros((1, 3, * self.size), dtype=numpy.float32)
        detection = self.session.run(None,
        {
            'input': dummy_input
        })  
        print("Arcface warmup complete: ", time.time() - st)

    def calc_embedding(self, temp_vision_frame, face_landmark_5):
        crop_vision_frame, matrix = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5)
        crop_vision_frame = crop_vision_frame / 127.5 - 1
        crop_vision_frame = crop_vision_frame[:, :, ::-1].transpose(2, 0, 1).astype(numpy.float32)
        crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0)
        embedding = self.forward(crop_vision_frame)
        embedding = embedding.ravel()
        normed_embedding = embedding / numpy.linalg.norm(embedding)
        embedding = numpy.expand_dims(embedding, 0)
        normed_embedding = numpy.expand_dims(normed_embedding, 0)
        
        return embedding, normed_embedding


    def forward(self, crop_vision_frame):
        embedding = self.session.run(None,
        {
            'input': crop_vision_frame
        })[0]

        return embedding