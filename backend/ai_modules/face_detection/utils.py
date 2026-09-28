import os
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


@dataclass
class Face:
    bounding_box: list
    landmark_5: list
    embedding: list
    normed_embedding: list
    gender: str
    age: int
    race: str
    id: str = None
    name: str = None


def draw_face_on_image(face: Face, image: np.ndarray):
    """
    Vẽ bounding box và tên lên ảnh dựa trên thông tin từ đối tượng Face.

    Parameters:
        face (Face): Đối tượng chứa thông tin về khuôn mặt.
        image (numpy.ndarray): Ảnh đầu vào (dạng ma trận numpy).

    Returns:
        numpy.ndarray: Ảnh với bounding box và tên đã được vẽ.
    """
    # Draw bounding box
    x1, y1, x2, y2 = map(int, face.bounding_box)

    if face.name:
        display_name = face.name
        color = (0, 255, 0)  # Green
    else:
        display_name = "Unknown"
        color = (0, 0, 255)  # Red

    # Draw bounding box
    cv2.rectangle(image, (x1, y1), (x2, y2), color=color, thickness=2)

    # Convert to PIL for text drawing
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)

    # Try to find a suitable font
    font_size = 24
    font = None
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu-sans/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu-sans/DejaVuSans.ttf",
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue

    if font is None:
        # Fallback to OpenCV if no suitable font found
        font_scale = 1
        font_thickness = 2
        text_x = x1
        text_y = y1 - 10 if y1 - 10 > 10 else y1 + 10
        cv2.putText(
            image,
            display_name,
            (text_x, text_y),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=font_scale,
            color=color,
            thickness=font_thickness,
        )
        return image

    # Draw text with PIL
    text_x = x1
    text_y = y1 - font_size if y1 - font_size > 10 else y1 + 10

    # Draw text background for better visibility
    text_bbox = draw.textbbox((text_x, text_y), display_name, font=font)
    draw.rectangle(
        [text_bbox[0] - 2, text_bbox[1] - 2, text_bbox[2] + 2, text_bbox[3] + 2],
        fill="black",
    )

    # Draw text
    draw.text(
        (text_x, text_y), display_name, fill=(color[0], color[1], color[2]), font=font
    )

    # Convert back to OpenCV format
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
