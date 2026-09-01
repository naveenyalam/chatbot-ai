from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import time
import hashlib
from app.models.document import Document, DocumentChunk
from app.services.embeddings import embeddings_provider
from app.core.metrics import (
    RAG_SEARCHES_TOTAL,
    RAG_SEARCH_DURATION,
    DB_OPS_TOTAL,
    RAG_RETRIEVAL_LATENCY,
    RAG_CHUNKS_RETURNED,
    RAG_CONTEXT_SIZE
)
from app.core.cache import NovaCache
from app.core.config import settings

def py_cosine_similarity(v1, v2):
    """
    Computes cosine similarity between two float lists in pure python.
    """
    if not v1 or not v2:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = sum(a * a for a in v1) ** 0.5
    norm_b = sum(b * b for b in v2) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


async def retrieve_relevant_chunks(
    db: Session,
    user_id: str,
    query: str,
    top_k: int = 5,
    document_ids: Optional[List[str]] = None,
    similarity_filtering: bool = True
) -> List[Dict[str, Any]]:
    """
    Fetches top K semantically similar chunks for a query from documents belonging to user.
    """
    start_time = time.time()
    status = "success"
    
    try:
        # Increment database operation counter
        DB_OPS_TOTAL.labels(op_type="query_rag", status="success").inc()
        
        # 1. Generate query vector embedding with cache reuse
        query_hash = hashlib.md5(query.strip().lower().encode("utf-8")).hexdigest()
        query_vector = NovaCache.get("embedding", query_hash)
        
        if not query_vector:
            query_vector = await embeddings_provider.embed_query(query)
            # Cache the embedding for 1 hour
            NovaCache.set("embedding", query_hash, query_vector, ttl=3600)

        dialect_name = db.bind.dialect.name
        results = []

        if dialect_name == "postgresql":
            # Native pgvector similarity calculation
            q = db.query(DocumentChunk).join(Document)
            q = q.filter(Document.user_id == user_id)
            if document_ids:
                q = q.filter(Document.id.in_(document_ids))
                
            distance = DocumentChunk.embedding.cosine_distance(query_vector)
            chunks = q.order_by(distance).limit(top_k).all()
            
            for chunk in chunks:
                sim = py_cosine_similarity(chunk.embedding, query_vector)
                # Apply relevance filtering
                min_score = settings.RAG_MIN_RELEVANCE_SCORE if similarity_filtering else -1.0
                if sim >= min_score:
                    results.append({
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "original_filename": chunk.document.original_filename,
                        "content": chunk.content,
                        "metadata": chunk.metadata_json,
                        "score": sim
                    })

        else:
            # SQLite in-memory evaluation fallback
            q = db.query(DocumentChunk).join(Document)
            q = q.filter(Document.user_id == user_id)
            if document_ids:
                q = q.filter(Document.id.in_(document_ids))
                
            chunks = q.all()
            scored = []
            for chunk in chunks:
                if not chunk.embedding:
                    continue
                sim = py_cosine_similarity(chunk.embedding, query_vector)
                # Apply relevance filtering
                min_score = settings.RAG_MIN_RELEVANCE_SCORE if similarity_filtering else -1.0
                if sim >= min_score:
                    scored.append((chunk, sim))
                
            scored.sort(key=lambda x: x[1], reverse=True)
            top_chunks = scored[:top_k]
            
            for chunk, sim in top_chunks:
                results.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "original_filename": chunk.document.original_filename,
                    "content": chunk.content,
                    "metadata": chunk.metadata_json,
                    "score": sim
                })

        # Record retrieval metrics
        elapsed = time.time() - start_time
        RAG_RETRIEVAL_LATENCY.observe(elapsed)
        RAG_CHUNKS_RETURNED.inc(len(results))
        RAG_CONTEXT_SIZE.inc(sum(len(c["content"]) for c in results))
        
        return results
            
    except Exception as exc:
        status = "error"
        DB_OPS_TOTAL.labels(op_type="query_rag", status="error").inc()
        raise exc
    finally:
        RAG_SEARCHES_TOTAL.labels(status=status).inc()
        RAG_SEARCH_DURATION.observe(time.time() - start_time)

