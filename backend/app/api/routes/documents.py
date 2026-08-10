import os
import uuid
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.document import Document
from app.services.auth_service import get_current_user
from app.storage import storage_provider
from app.services.document_service import process_document_in_background

from app.core.rate_limit import RateLimiter
from app.core.idempotency import check_idempotency, save_idempotency_response

router = APIRouter(prefix="/documents", tags=["documents"])

from app.core.config import settings

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv", ".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB limit

upload_limiter = RateLimiter(requests=settings.RATE_LIMIT_UPLOAD, window=60, key_prefix="upload")

@router.post("/upload", status_code=status.HTTP_201_CREATED, dependencies=[Depends(upload_limiter)])
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check idempotency first
    cached_resp = check_idempotency(request)
    if cached_resp:
        return cached_resp
    # 1. Validate file exists and is not empty
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    # Prevent path traversal attempts in filename
    if ".." in file.filename or "/" in file.filename or "\\" in file.filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename. Directory traversal characters are not permitted."
        )

    # 2. Validate file extension
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {', '.join(e[1:].upper() for e in SUPPORTED_EXTENSIONS)}"
        )

    # Enforce global files limit per user
    existing_count = db.query(Document).filter(Document.user_id == current_user.id).count()
    if existing_count >= settings.MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum document storage limit reached ({settings.MAX_FILES_PER_REQUEST} files)."
        )

    # 3. Read content to validate size
    try:
        content = await file.read()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read file payload."
        )

    file_size = len(content)
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty."
        )
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )

    # Validate file signatures to prevent disguised executables / scripts
    if ext == ".pdf":
        if not content.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="Invalid PDF file signature.")
    elif ext in (".jpg", ".jpeg"):
        if not content.startswith(b"\xff\xd8\xff"):
            raise HTTPException(status_code=400, detail="Invalid JPEG image signature.")
    elif ext == ".png":
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(status_code=400, detail="Invalid PNG image signature.")
    elif ext == ".webp":
        if not (content.startswith(b"RIFF") and b"WEBP" in content[8:16]):
            raise HTTPException(status_code=400, detail="Invalid WEBP image signature.")
    elif ext == ".docx":
        if not content.startswith(b"PK\x03\x04"):
            raise HTTPException(status_code=400, detail="Invalid DOCX file signature.")
    elif ext in (".txt", ".md", ".csv"):
        if b"\x00" in content[:1024]:
            raise HTTPException(status_code=400, detail="Text files must not contain binary data.")

    # Validate image properties and corruption via Pillow
    is_image = ext in {".png", ".jpg", ".jpeg", ".webp"}
    if is_image:
        max_img_size = settings.VISION_MAX_IMAGE_SIZE_MB * 1024 * 1024
        if file_size > max_img_size:
            raise HTTPException(
                status_code=400,
                detail=f"Image exceeds maximum size of {settings.VISION_MAX_IMAGE_SIZE_MB}MB."
            )
        import io
        from PIL import Image
        try:
            with Image.open(io.BytesIO(content)) as img:
                img.verify()  # check corruption
                width, height = img.size
                if width < 16 or height < 16:
                    raise ValueError("Image dimensions too small (minimum 16x16 pixels required).")
                if width > 8192 or height > 8192:
                    raise ValueError("Image dimensions too large (maximum 8192x8192 pixels allowed).")
        except Exception as img_err:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or corrupted image: {str(img_err)}"
            )

    # 4. Generate safe unique path name and save on disk (isolated by user folder)
    safe_filename = f"{uuid.uuid4()}{ext}"
    isolated_filename = f"user_{current_user.id}/{safe_filename}"
    try:
        storage_path = storage_provider.save_file(content, isolated_filename)
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"File storage failed: {err}"
        )

    # 5. Insert document metadata record
    doc = Document(
        user_id=current_user.id,
        filename=safe_filename,
        original_filename=file.filename,
        mime_type=file.content_type or ("image/" + ext[1:] if is_image else "application/octet-stream"),
        file_size=file_size,
        storage_path=storage_path,
        status="indexed" if is_image else "uploaded",
        page_count=1 if is_image else 0
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 6. Trigger background extraction and vector indexing only if NOT an image
    if not is_image:
        from app.core.jobs import enqueue_job
        background_tasks.add_task(enqueue_job, "process_document", {"document_id": doc.id})

    res_data = {
        "id": doc.id,
        "original_filename": doc.original_filename,
        "mime_type": doc.mime_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "page_count": doc.page_count,
        "created_at": doc.created_at.isoformat() if doc.created_at else None
    }
    save_idempotency_response(request, json.dumps(res_data).encode(), 201)
    return res_data


@router.get("", response_model=None)
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    docs = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.created_at.desc()).all()

    return [
        {
            "id": d.id,
            "original_filename": d.original_filename,
            "mime_type": d.mime_type,
            "file_size": d.file_size,
            "status": d.status,
            "page_count": d.page_count,
            "created_at": d.created_at
        }
        for d in docs
    ]


@router.get("/{id}")
def get_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == id,
        Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {
        "id": doc.id,
        "original_filename": doc.original_filename,
        "mime_type": doc.mime_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "page_count": doc.page_count,
        "created_at": doc.created_at
    }


@router.get("/{id}/status")
def get_document_status(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == id,
        Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {
        "id": doc.id,
        "status": doc.status,
        "page_count": doc.page_count
    }


@router.delete("/{id}")
def delete_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == id,
        Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove file from disk storage
    try:
        storage_provider.delete_file(doc.storage_path)
    except Exception as err:
        print(f"Error deleting file from storage: {err}")

    # Remove database entries (chunks deleted via cascade)
    db.delete(doc)
    db.commit()

    return {"status": "success", "message": "Document deleted."}
