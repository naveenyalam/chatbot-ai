import httpx
import random
from typing import List
from app.services.embeddings.base import BaseEmbeddings
from app.core.config import settings

class OpenAIEmbeddings(BaseEmbeddings):
    def __init__(self):
        self.api_key = settings.AI_API_KEY
        self.base_url = settings.AI_BASE_URL or "https://api.openai.com/v1"
        self.model = "text-embedding-3-small"

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # If API key is placeholder or empty, fallback to deterministic mock vectors
        if not self.api_key or "your-api-key" in self.api_key.lower():
            return [self._get_mock_embedding(t) for t in texts]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"input": texts, "model": self.model},
                    timeout=30.0
                )
                if response.status_code == 200:
                    res_json = response.json()
                    return [item["embedding"] for item in res_json["data"]]
                else:
                    print(f"Embeddings API error {response.status_code}: {response.text}")
                    return [self._get_mock_embedding(t) for t in texts]
        except Exception as err:
            print(f"Embeddings connection error: {err}. Using mock fallback.")
            return [self._get_mock_embedding(t) for t in texts]

    async def embed_query(self, text: str) -> List[float]:
        res = await self.embed_documents([text])
        return res[0]

    def _get_mock_embedding(self, text: str) -> List[float]:
        # Generate stable normalized vector based on character sum seed
        val_seed = sum(ord(c) for c in text)
        random.seed(val_seed)
        vec = [random.uniform(-1.0, 1.0) for _ in range(1536)]
        norm = sum(v * v for v in vec) ** 0.5
        if norm == 0:
            return vec
        return [v / norm for v in vec]
