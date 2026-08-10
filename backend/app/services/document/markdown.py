from app.services.document.txt import TxtExtractor

class MarkdownExtractor(TxtExtractor):
    """
    Markdown extractor. Reuses textual parsing logic since markdown text is raw text.
    """
    pass
