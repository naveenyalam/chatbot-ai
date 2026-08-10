from app.storage.base import BaseStorage
from app.storage.local_storage import LocalStorage

# Expose storage adapter instance for use globally in routes and jobs
storage_provider = LocalStorage()

__all__ = ["BaseStorage", "LocalStorage", "storage_provider"]
