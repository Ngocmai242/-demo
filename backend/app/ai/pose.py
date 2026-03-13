import io
import os
import urllib.request
from PIL import Image
import numpy as np

def _load_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(img)

def extract_keypoints(image_bytes, max_people=2):
    """
    Extracts keypoints for up to `max_people` in an image.
    Returns a list of dictionaries (one per person) or (None, error_string).
    """
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision as mp_vision
    except Exception as e:
        return None, f"mediapipe_error:{e}"

    img_np = _load_image(image_bytes)
    h, w = img_np.shape[:2]

    model_dir = os.path.join(os.path.dirname(__file__), "models")
    model_path = os.path.join(model_dir, "pose_landmarker_heavy.task") # Using heavy model for better accuracy

    if not os.path.exists(model_path):
        try:
            os.makedirs(model_dir, exist_ok=True)
            # Using the 'heavy' model is better for multi-person detection
            url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task"
            urllib.request.urlretrieve(url, model_path)
        except Exception as e:
            return None, f"mediapipe_error:download_model_failed:{e}"

    try:
        BaseOptions = mp_python.BaseOptions
        PoseLandmarker = mp_vision.PoseLandmarker
        PoseLandmarkerOptions = mp_vision.PoseLandmarkerOptions
        VisionRunningMode = mp_vision.RunningMode

        # Configure for multiple poses
        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.IMAGE,
            num_poses=max_people # Key change: detect multiple people
        )

        with PoseLandmarker.create_from_options(options) as landmarker:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_np)
            result = landmarker.detect(mp_image)

            if not result.pose_landmarks:
                return [], "no_pose" # Return empty list if no one is detected

            all_people_points = []
            for person_landmarks in result.pose_landmarks:
                def get_xy_idx(i):
                    p = person_landmarks[i]
                    return int(p.x * w), int(p.y * h)
                
                points = {
                    "left_shoulder": get_xy_idx(11),
                    "right_shoulder": get_xy_idx(12),
                    "left_hip": get_xy_idx(23),
                    "right_hip": get_xy_idx(24),
                    "left_ankle": get_xy_idx(27),
                    "right_ankle": get_xy_idx(28),
                    "nose": get_xy_idx(0)
                }
                all_people_points.append(points)
            
            return all_people_points, None

    except Exception as e:
        return None, f"mediapipe_error:tasks_infer_failed:{e}"
