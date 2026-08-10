import os
import csv
from typing import Dict, Any
from app.services.document.base import BaseExtractor

class CSVExtractor(BaseExtractor):
    def extract(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        row_segments = []
        headers = []
        
        # Read file with encoding fallbacks
        try:
            with open(file_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                headers = [h.strip() for h in next(reader, [])]
                for idx, row in enumerate(reader):
                    cols = [cell.strip() for cell in row]
                    pairs = []
                    for h, val in zip(headers, cols):
                        if val:
                            pairs.append(f"{h}: {val}")
                    if pairs:
                        row_segments.append(f"Record {idx + 1}:\n" + "\n".join(pairs))
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1", newline="") as f:
                reader = csv.reader(f)
                headers = [h.strip() for h in next(reader, [])]
                for idx, row in enumerate(reader):
                    cols = [cell.strip() for cell in row]
                    pairs = []
                    for h, val in zip(headers, cols):
                        if val:
                            pairs.append(f"{h}: {val}")
                    if pairs:
                        row_segments.append(f"Record {idx + 1}:\n" + "\n".join(pairs))

        full_text = "\n\n".join(row_segments).strip()
        if not full_text:
            full_text = "This CSV file is empty."
            
        return {
            "text": full_text,
            "pages": [{"page_number": 1, "text": full_text}],
            "metadata": {
                "row_count": len(row_segments),
                "headers": headers
            }
        }
