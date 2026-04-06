"""Face verification utility using face_recognition library."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

from config import FACE_MATCH_TOLERANCE, KNOWN_FACES_DIR


def _decode_base64_image(image_base64: str) -> bytes:
    if "," in image_base64:
        image_base64 = image_base64.split(",", maxsplit=1)[1]
    return base64.b64decode(image_base64)


def verify_employee_face(employee_id: int, image_base64: Optional[str] = None, image_path: Optional[str] = None) -> tuple[bool, str]:
    """Verify uploaded face with stored face embedding for employee.

    Returns:
        (True, "Matched") on success, otherwise (False, reason).
    """
    known_img_path = KNOWN_FACES_DIR / f"{employee_id}.jpg"
    if not known_img_path.exists():
        return False, f"No registered face for employee_id={employee_id}."

    try:
        import face_recognition
        import numpy as np

        known_image = face_recognition.load_image_file(str(known_img_path))
        known_encodings = face_recognition.face_encodings(known_image)
        if not known_encodings:
            return False, "Stored face image has no detectable face."

        known_encoding = known_encodings[0]

        unknown_image = None
        if image_base64:
            raw = _decode_base64_image(image_base64)
            # Convert raw bytes to image matrix
            arr = np.frombuffer(raw, dtype=np.uint8)
            import cv2

            unknown_image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if unknown_image is not None:
                unknown_image = unknown_image[:, :, ::-1]  # BGR -> RGB
        elif image_path:
            unknown_image = face_recognition.load_image_file(image_path)

        if unknown_image is None:
            return False, "No attendance image provided."

        unknown_encodings = face_recognition.face_encodings(unknown_image)
        if not unknown_encodings:
            return False, "No face detected in attendance image."

        distance = face_recognition.face_distance([known_encoding], unknown_encodings[0])[0]
        matched = distance <= FACE_MATCH_TOLERANCE
        if matched:
            return True, "Face matched."

        return False, f"Face mismatch (distance={distance:.3f})."

    except ImportError:
        return False, "face_recognition dependencies missing. Install requirements first."
    except Exception as exc:  # noqa: BLE001
        return False, f"Face verification failed: {exc}"


def save_uploaded_image(file_storage, target_path: Path) -> str:
    """Save uploaded file from Flask request and return final path string."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    file_storage.save(target_path)
    return str(target_path)
