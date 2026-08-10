import abc
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    published_at: Optional[datetime] = None

class SearchProvider(abc.ABC):
    @abc.abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Execute a search query and return a list of normalized SearchResult objects.
        """
        pass
