from app.services.embeddings.base import BaseEmbeddings
from app.services.embeddings.provider import OpenAIEmbeddings

# Singleton provider instance
embeddings_provider = OpenAIEmbeddings()

__all__ = ["BaseEmbeddings", "OpenAIEmbeddings", "embeddings_provider"]
