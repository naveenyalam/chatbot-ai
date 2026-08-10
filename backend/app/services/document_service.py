import os
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentChunk
from app.services.document import get_extractor
from app.services.embeddings import embeddings_provider

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
MAX_CHUNKS_PER_DOCUMENT = 10000

def clean_text(text: str) -> str:
    """
    Normalizes excessive whitespace and removes broken control characters.
    """
    if not text:
        return ""
    # Clean non-printable characters except newlines/tabs
    cleaned = "".join(c for c in text if c.isprintable() or c in "\n\r\t")
    return cleaned.strip()


def chunk_document_pages(pages: list, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """
    Chunks document page-by-page to preserve citation boundaries.
    """
    chunks = []
    for page in pages:
        page_num = page.get("page_number", 1)
        text = clean_text(page.get("text", ""))
        if not text:
            continue
            
        idx = 0
        while idx < len(text):
            chunk_text = text[idx : idx + chunk_size].strip()
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "metadata": {
                        "page": page_num
                    }
                })
            # Slide window
            idx += (chunk_size - overlap)
            # Avoid duplicate trailing chunks if remaining characters are too small
            if len(text) - idx < overlap:
                break
                
    return chunks


async def process_document_in_background(db: Session, document_id: str):
    """
    Loads, parses, chunks, embeds, and indexes an uploaded file.
    """
    # 1. Fetch document record
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        print(f"Document {document_id} not found in database.")
        return

    doc.status = "processing"
    db.commit()

    try:
        if not os.path.exists(doc.storage_path):
            raise FileNotFoundError(f"Storage path {doc.storage_path} does not exist.")

        # 2. Extract content
        _, ext = os.path.splitext(doc.original_filename)
        extractor = get_extractor(ext)
        if not extractor:
            raise ValueError(f"No extractor registered for suffix: {ext}")

        extracted = extractor.extract(doc.storage_path)
        doc.page_count = extracted.get("metadata", {}).get("page_count", 1)
        db.commit()

        # 3. Create Chunks
        chunks_data = chunk_document_pages(extracted["pages"])
        if len(chunks_data) > MAX_CHUNKS_PER_DOCUMENT:
            raise ValueError(
                f"Document chunk count ({len(chunks_data)}) exceeds resource limit of {MAX_CHUNKS_PER_DOCUMENT}"
            )

        if not chunks_data:
            # Seed a single blank record if nothing extracted
            chunks_data = [{"content": "This document contains no readable text content.", "metadata": {"page": 1}}]

        # 4. Generate Embeddings in batches
        texts_to_embed = [c["content"] for c in chunks_data]
        embeddings = await embeddings_provider.embed_documents(texts_to_embed)

        # 5. Insert Chunks
        for idx, (chunk, emb) in enumerate(zip(chunks_data, embeddings)):
            db_chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk["content"],
                metadata_json={
                    "page": chunk["metadata"]["page"],
                    "source": doc.original_filename
                },
                embedding=emb
            )
            db.add(db_chunk)

        doc.status = "indexed"
        db.commit()
        print(f"Successfully indexed document {doc.original_filename} ({len(chunks_data)} chunks)")

    except Exception as err:
        db.rollback()
        doc.status = "failed"
        db.commit()
        print(f"Failed to process document {document_id}: {err}")
