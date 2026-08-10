import os
from app.storage.base import BaseStorage

class LocalStorage(BaseStorage):
    def __init__(self, upload_dir: str = None):
        if upload_dir is None:
            # Locate storage/uploads relative to backend root
            backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            self.upload_dir = os.path.join(backend_root, "storage", "uploads")
        else:
            self.upload_dir = os.path.abspath(upload_dir)
            
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_file(self, file_content: bytes, filename: str) -> str:
        # Resolve target path and verify sandbox constraints to prevent traversal attacks
        target_path = os.path.abspath(os.path.join(self.upload_dir, filename))
        if not target_path.startswith(self.upload_dir):
            raise ValueError("Path traversal attempt blocked.")
            
        # Ensure user subdirectories or other folders exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
        with open(target_path, "wb") as f:
            f.write(file_content)
        return target_path

    def delete_file(self, storage_path: str) -> None:
        abs_path = os.path.abspath(storage_path)
        if not abs_path.startswith(self.upload_dir):
            raise ValueError("Unauthorized file deletion request.")
            
        if os.path.exists(abs_path):
            os.remove(abs_path)
