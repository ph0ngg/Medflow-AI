import cv2
import numpy as np

warp_template = np.array([
            [38.2946, 51.6963], 
            [73.5318, 51.5014], 
            [56.0252, 71.7366],
            [41.5493, 92.3655], 
            [70.7299, 92.2041]], dtype=np.float32)

crop_size = (112, 112)

def estimate_matrix_by_face_landmark_5(face_landmark_5):
	affine_matrix = cv2.estimateAffinePartial2D(face_landmark_5, warp_template, method = cv2.RANSAC, ransacReprojThreshold = 100)[0]
	return affine_matrix

def warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5):
    affine_matrix = estimate_matrix_by_face_landmark_5(face_landmark_5)
    crop_vision_frame = cv2.warpAffine(temp_vision_frame, affine_matrix, crop_size, borderMode = cv2.BORDER_REFLECT, flags = cv2.INTER_AREA)
	
    return crop_vision_frame, affine_matrix