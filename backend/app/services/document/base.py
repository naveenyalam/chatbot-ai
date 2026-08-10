import abc
from typing import Dict, List, Any

class BaseExtractor(abc.ABC):
    @abc.abstractmethod
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extracts text content and returns structure containing:
        - "text": str (full combined text)
        - "pages": List[Dict[str, Any]] where each item has {"page_number": int, "text": str}
        - "metadata": Dict[str, Any]
        """
        pass
