import os
from typing import Dict, Any
from app.services.document.base import BaseExtractor

class TxtExtractor(BaseExtractor):
    def extract(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                text = f.read()
                
        text_clean = text.strip()
        if not text_clean:
            text_clean = "This text document is empty."
            
        return {
            "text": text_clean,
            "pages": [{"page_number": 1, "text": text_clean}],
            "metadata": {
                "character_count": len(text_clean)
            }
        }
