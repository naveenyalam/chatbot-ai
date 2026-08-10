import os
from typing import Dict, Any
from pypdf import PdfReader
from app.services.document.base import BaseExtractor

class PDFExtractor(BaseExtractor):
    def extract(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        reader = PdfReader(file_path)
        pages = []
        full_text_parts = []
        
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text_clean = text.strip()
            pages.append({
                "page_number": idx + 1,
                "text": text_clean
            })
            if text_clean:
                full_text_parts.append(text_clean)
                
        full_text = "\n\n".join(full_text_parts).strip()
        
        # Guard for scanned documents
        if not full_text:
            warn_msg = "This document appears to contain scanned images. OCR is not currently enabled for this file."
            full_text = warn_msg
            pages = [{"page_number": 1, "text": warn_msg}]
            
        return {
            "text": full_text,
            "pages": pages,
            "metadata": {
                "page_count": len(reader.pages)
            }
        }
