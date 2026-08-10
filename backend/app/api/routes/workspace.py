import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, select

from app.db.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document
from app.models.workspace import Collection, Prompt, SavedResponse, Notification, WorkspacePreference, document_collections
from app.api.routes.auth import get_current_user

logger = logging.getLogger("nova-ai.workspace-routes")

router = APIRouter()

# --- Schemas ---

class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field("#6366f1", max_length=30)

class CollectionAddDocument(BaseModel):
    document_id: str

class PromptCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    content: str = Field(..., min_length=1)
    category: str = Field("Productivity", max_length=50)
    variables: Optional[List[str]] = Field(default_factory=list)

class PromptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    is_favorite: Optional[bool] = None

class SavedResponseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    content: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    category: Optional[str] = "General"

class PreferenceUpdate(BaseModel):
    default_workspace: Optional[str] = "chat"
    default_model: Optional[str] = "intelligence"
    response_detail: Optional[str] = "balanced"
    response_tone: Optional[str] = "professional"
    language: Optional[str] = "en"
    composer_behavior: Optional[str] = "enter_send"

class NotificationMarkRead(BaseModel):
    ids: Optional[List[str]] = None
    mark_all: Optional[bool] = False


# --- Collections Endpoints ---

@router.get("/collections")
def list_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    collections = db.query(Collection).filter(Collection.user_id == current_user.id).order_by(desc(Collection.created_at)).all()
    results = []
    for c in collections:
        doc_count = db.query(document_collections).filter(document_collections.c.collection_id == c.id).count()
        results.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "color": c.color,
            "document_count": doc_count,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    return results

@router.post("/collections", status_code=status.HTTP_201_CREATED)
def create_collection(
    body: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    collection = Collection(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        color=body.color or "#6366f1"
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return {
        "id": collection.id,
        "name": collection.name,
        "description": collection.description,
        "color": collection.color,
        "document_count": 0,
        "created_at": collection.created_at.isoformat()
    }

@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    col = db.query(Collection).filter(Collection.id == collection_id, Collection.user_id == current_user.id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")
    db.delete(col)
    db.commit()
    return None

@router.post("/collections/{collection_id}/documents")
def add_document_to_collection(
    collection_id: str,
    body: CollectionAddDocument,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    col = db.query(Collection).filter(Collection.id == collection_id, Collection.user_id == current_user.id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")
    doc = db.query(Document).filter(Document.id == body.document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc not in col.documents:
        col.documents.append(doc)
        db.commit()
    return {"status": "success", "message": f"Document added to collection {col.name}"}


# --- Prompts Endpoints ---

@router.get("/prompts")
def list_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prompts = db.query(Prompt).filter(Prompt.user_id == current_user.id).order_by(desc(Prompt.is_favorite), desc(Prompt.created_at)).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "category": p.category,
            "is_favorite": p.is_favorite,
            "variables": p.variables or [],
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in prompts
    ]

@router.post("/prompts", status_code=status.HTTP_201_CREATED)
def create_prompt(
    body: PromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prompt = Prompt(
        user_id=current_user.id,
        title=body.title,
        content=body.content,
        category=body.category,
        variables=body.variables or []
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return {
        "id": prompt.id,
        "title": prompt.title,
        "content": prompt.content,
        "category": prompt.category,
        "is_favorite": prompt.is_favorite,
        "variables": prompt.variables,
        "created_at": prompt.created_at.isoformat()
    }

@router.patch("/prompts/{prompt_id}")
def update_prompt(
    prompt_id: str,
    body: PromptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Prompt).filter(Prompt.id == prompt_id, Prompt.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Prompt not found.")

    if body.title is not None: p.title = body.title
    if body.content is not None: p.content = body.content
    if body.category is not None: p.category = body.category
    if body.is_favorite is not None: p.is_favorite = body.is_favorite

    db.commit()
    return {
        "id": p.id,
        "title": p.title,
        "content": p.content,
        "category": p.category,
        "is_favorite": p.is_favorite,
        "variables": p.variables,
        "created_at": p.created_at.isoformat()
    }

@router.delete("/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(
    prompt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Prompt).filter(Prompt.id == prompt_id, Prompt.user_id == current_user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Prompt not found.")
    db.delete(p)
    db.commit()
    return None


# --- Saved Responses Endpoints ---

@router.get("/saved-responses")
def list_saved_responses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = db.query(SavedResponse).filter(SavedResponse.user_id == current_user.id).order_by(desc(SavedResponse.created_at)).all()
    return [
        {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "conversation_id": item.conversation_id,
            "message_id": item.message_id,
            "category": item.category,
            "is_favorite": item.is_favorite,
            "created_at": item.created_at.isoformat() if item.created_at else None
        }
        for item in items
    ]

@router.post("/saved-responses", status_code=status.HTTP_201_CREATED)
def create_saved_response(
    body: SavedResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = SavedResponse(
        user_id=current_user.id,
        title=body.title,
        content=body.content,
        conversation_id=body.conversation_id,
        message_id=body.message_id,
        category=body.category or "General"
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "conversation_id": item.conversation_id,
        "message_id": item.message_id,
        "category": item.category,
        "is_favorite": item.is_favorite,
        "created_at": item.created_at.isoformat()
    }

@router.delete("/saved-responses/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_response(
    response_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(SavedResponse).filter(SavedResponse.id == response_id, SavedResponse.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Saved response not found.")
    db.delete(item)
    db.commit()
    return None


# --- Notifications Endpoints ---

@router.get("/notifications")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.is_read.asc(), desc(Notification.created_at)).limit(50).all()
    unread_count = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).count()
    return {
        "unread_count": unread_count,
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "category": n.category,
                "is_read": n.is_read,
                "link": n.link,
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            for n in items
        ]
    }

@router.post("/notifications/mark-read")
def mark_notifications_read(
    body: NotificationMarkRead,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if body.mark_all:
        db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).update({"is_read": True})
    elif body.ids:
        db.query(Notification).filter(Notification.user_id == current_user.id, Notification.id.in_(body.ids)).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"status": "success"}


# --- Preferences Endpoints ---

@router.get("/preferences")
def get_user_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pref = db.query(WorkspacePreference).filter(WorkspacePreference.user_id == current_user.id).first()
    if not pref:
        pref = WorkspacePreference(user_id=current_user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return {
        "default_workspace": pref.default_workspace,
        "default_model": pref.default_model,
        "response_detail": pref.response_detail,
        "response_tone": pref.response_tone,
        "language": pref.language,
        "composer_behavior": pref.composer_behavior
    }

@router.put("/preferences")
def update_user_preferences(
    body: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pref = db.query(WorkspacePreference).filter(WorkspacePreference.user_id == current_user.id).first()
    if not pref:
        pref = WorkspacePreference(user_id=current_user.id)
        db.add(pref)

    if body.default_workspace is not None: pref.default_workspace = body.default_workspace
    if body.default_model is not None: pref.default_model = body.default_model
    if body.response_detail is not None: pref.response_detail = body.response_detail
    if body.response_tone is not None: pref.response_tone = body.response_tone
    if body.language is not None: pref.language = body.language
    if body.composer_behavior is not None: pref.composer_behavior = body.composer_behavior

    db.commit()
    return {
        "status": "success",
        "preferences": {
            "default_workspace": pref.default_workspace,
            "default_model": pref.default_model,
            "response_detail": pref.response_detail,
            "response_tone": pref.response_tone,
            "language": pref.language,
            "composer_behavior": pref.composer_behavior
        }
    }


# --- Unified Global Search Endpoint ---

@router.get("/search")
def unified_search(
    q: str = Query(..., min_length=2, max_length=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query_str = f"%{q}%"

    # Search conversations
    convs = db.query(Conversation).filter(
        Conversation.user_id == current_user.id,
        Conversation.title.ilike(query_str)
    ).limit(8).all()

    # Search documents
    docs = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.original_filename.ilike(query_str)
    ).limit(8).all()

    # Search prompts
    prompts = db.query(Prompt).filter(
        Prompt.user_id == current_user.id,
        or_(Prompt.title.ilike(query_str), Prompt.content.ilike(query_str))
    ).limit(8).all()

    # Search saved responses
    saved = db.query(SavedResponse).filter(
        SavedResponse.user_id == current_user.id,
        or_(SavedResponse.title.ilike(query_str), SavedResponse.content.ilike(query_str))
    ).limit(8).all()

    return {
        "conversations": [{"id": c.id, "title": c.title, "type": "conversation"} for c in convs],
        "documents": [{"id": d.id, "name": d.original_filename, "type": "document"} for d in docs],
        "prompts": [{"id": p.id, "title": p.title, "type": "prompt"} for p in prompts],
        "saved_responses": [{"id": s.id, "title": s.title, "type": "saved_response"} for s in saved]
    }
