from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
from app.database import get_db
from app.models import Ticket, Comment, Category
from app.schemas import KnowledgeBaseResponse, KnowledgeBaseEntry

router = APIRouter(prefix="/api", tags=["knowledge-base"])


@router.get("/knowledge-base", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Knowledge base derived from resolved tickets with resolutions/comments.
    Only returns tickets that have useful resolution or comment information.
    """
    query = (
        db.query(Ticket)
        .options(joinedload(Ticket.category), joinedload(Ticket.comments))
        .filter(Ticket.status == "resolved")
    )

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Ticket.summary.ilike(search_term),
                Ticket.description.ilike(search_term),
            )
        )

    if category_id is not None:
        query = query.filter(Ticket.category_id == category_id)

    total = query.count()
    offset = (page - 1) * page_size
    tickets = query.order_by(Ticket.resolved_at.desc().nullslast()).offset(offset).limit(page_size).all()

    entries = []
    for t in tickets:
        # Gather useful comment highlights (internal notes preferred)
        highlights = []
        if t.comments:
            internal = [c.body for c in t.comments if c.visibility == "internal" and c.body]
            public = [c.body for c in t.comments if c.visibility == "public" and c.body]
            highlights = (internal[:3] if internal else public[:3])

        entries.append(KnowledgeBaseEntry(
            ticket_id=t.id,
            summary=t.summary,
            description=t.description,
            category_name=t.category.name if t.category else None,
            resolution=t.resolution,
            comment_highlights=highlights,
        ))

    return KnowledgeBaseResponse(entries=entries, total=total)
