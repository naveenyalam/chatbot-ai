import abc

class MultimodalProvider(abc.ABC):
    @abc.abstractmethod
    async def analyze(self, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        """
        Analyze an image with a text prompt and return the analysis response text.
        """
        pass
