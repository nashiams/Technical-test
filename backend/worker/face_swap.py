import insightface
from insightface.app import FaceAnalysis
from PIL import Image
import numpy as np

assert insightface.__version__ >= '0.7'

def prepare_app():
    """Initialize face analysis app and swapper model"""
    app = FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=0, det_size=(640, 640))
    swapper = insightface.model_zoo.get_model('inswapper_128.onnx', download=False, download_zip=False)
    return app, swapper

def sort_faces(faces):
    """Sort faces by x-coordinate (left to right)"""
    return sorted(faces, key=lambda x: x.bbox[0])

def get_face(faces, face_id):
    """Get specific face by index (1-based)"""
    if len(faces) < face_id or face_id < 1:
        raise Exception(f"The image includes only {len(faces)} faces, however, you asked for face {face_id}")
    return faces[face_id-1]

def swap_faces(app, swapper, source_img_path, dest_img_path, source_face_idx=1, dest_face_idx=1):
    """
    Perform face swap between two images
    Args:
        app: FaceAnalysis instance
        swapper: Face swapper model
        source_img_path: Path to source image (face to use)
        dest_img_path: Path to destination image (face to replace)
        source_face_idx: Index of face in source image (1-based)
        dest_face_idx: Index of face in destination image (1-based)
    Returns:
        numpy array of result image
    """
    # Load images
    source_img = np.array(Image.open(source_img_path))
    dest_img = np.array(Image.open(dest_img_path))
    
    # Get faces from source image
    faces = sort_faces(app.get(source_img))
    if not faces:
        raise Exception("No faces found in source image")
    source_face = get_face(faces, source_face_idx)
    
    # Get faces from destination image
    res_faces = sort_faces(app.get(dest_img))
    if not res_faces:
        raise Exception("No faces found in destination image")
    res_face = get_face(res_faces, dest_face_idx)
    
    # Perform face swap
    result = swapper.get(dest_img, res_face, source_face, paste_back=True)
    return result