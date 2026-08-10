from app.services.document.pdf import PDFExtractor
from app.services.document.docx import DocxExtractor
from app.services.document.txt import TxtExtractor
from app.services.document.markdown import MarkdownExtractor
from app.services.document.csv import CSVExtractor

EXTRACTORS = {
    ".pdf": PDFExtractor(),
    ".docx": DocxExtractor(),
    ".txt": TxtExtractor(),
    ".md": MarkdownExtractor(),
    ".csv": CSVExtractor()
}

def get_extractor(extension: str):
    """
    Returns appropriate document parser extractor instance based on suffix name.
    """
    return EXTRACTORS.get(extension.lower())
