import abc
from typing import List

class BaseEmbeddings(abc.ABC):
    @abc.abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generates dense vector embeddings for a list of document texts.
        """
        pass

    @abc.abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """
        Generates a dense vector embedding for a single search query string.
        """
        pass
