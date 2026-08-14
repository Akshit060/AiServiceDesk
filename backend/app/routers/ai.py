from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app.models import Ticket, Category, Comment
from app.schemas import (
    AIAnalysisResponse, AIClassifyResponse, AIErrorResponse, RelatedTicketResponse,
    AIResolutionDraftResponse, AIChatRequest, AIChatResponse
)
from app.services.ai_service import get_ai_service
from app.services.retrieval_service import find_related_tickets
from app.services.embedding_service import get_embedding_service

router = APIRouter(prefix="/api", tags=["ai"])

class ClassifyRequest(BaseModel):
    summary: str
    description: str

def _get_ticket_context(db: Session, ticket_id: int):
    ticket = (
        db.query(Ticket)
        .options(
            joinedload(Ticket.category),
            joinedload(Ticket.assigned_agent),
            joinedload(Ticket.comments).joinedload(Comment.agent),
        )
        .filter(Ticket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")

    related = find_related_tickets(
        db=db,
        ticket_id=ticket.id,
        summary=ticket.summary,
        description=ticket.description,
        category_id=ticket.category_id,
    )

    ticket_dict = {
        "summary": ticket.summary,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "category_name": ticket.category.name if ticket.category else "Uncategorized",
    }
    comments_list = [
        {"agent_name": c.agent.name if c.agent else "Unknown", "body": c.body}
        for c in (ticket.comments or [])
    ]
    return ticket_dict, comments_list, related

@router.post("/tickets/{ticket_id}/analyze")
def analyze_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """AI-powered ticket analysis with semantic RAG context."""
    ai_service = get_ai_service()
    if not ai_service.is_available():
        return AIErrorResponse(available=False, error="AI analysis is currently unavailable. Please configure GROQ_API_KEY.")

    try:
        ticket_dict, comments_list, related = _get_ticket_context(db, ticket_id)
        analysis = ai_service.analyze_ticket(ticket_dict, comments_list, related)

        return {
            "available": True,
            "analysis": analysis.model_dump(),
            "related_tickets": related,
        }
    except ValueError as e:
        return AIErrorResponse(available=False, error=str(e))
    except Exception as e:
        return AIErrorResponse(available=False, error=f"AI analysis failed unexpectedly: {str(e)}")


@router.post("/tickets/classify")
def classify_ticket(data: ClassifyRequest, db: Session = Depends(get_db)):
    """AI-assisted ticket classification."""
    ai_service = get_ai_service()
    if not ai_service.is_available():
        return AIErrorResponse(available=False, error="AI classification is currently unavailable. Please configure GROQ_API_KEY.")

    try:
        categories = [c.name for c in db.query(Category).all()]
        result = ai_service.classify_ticket(data.summary, data.description, categories)
        return {"available": True, "classification": result.model_dump()}
    except ValueError as e:
        return AIErrorResponse(available=False, error=str(e))
    except Exception as e:
        return AIErrorResponse(available=False, error=f"AI classification failed: {str(e)}")


@router.get("/tickets/{ticket_id}/related", response_model=List[RelatedTicketResponse])
def get_related_tickets(ticket_id: int, db: Session = Depends(get_db)):
    """Get related historical tickets (Semantic Search)."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")

    related = find_related_tickets(
        db=db,
        ticket_id=ticket.id,
        summary=ticket.summary,
        description=ticket.description,
        category_id=ticket.category_id,
    )
    return related


@router.post("/tickets/{ticket_id}/generate-resolution", response_model=AIResolutionDraftResponse)
def generate_resolution_draft(ticket_id: int, db: Session = Depends(get_db)):
    """AI-generated resolution draft based on incident context and RAG."""
    ai_service = get_ai_service()
    if not ai_service.is_available():
        return AIResolutionDraftResponse(available=False, error="AI resolution drafting is unavailable. Please configure GROQ_API_KEY.")

    try:
        ticket_dict, comments_list, related = _get_ticket_context(db, ticket_id)
        draft = ai_service.generate_resolution_draft(ticket_dict, comments_list, related)
        return AIResolutionDraftResponse(available=True, draft=draft)
    except ValueError as e:
        return AIResolutionDraftResponse(available=False, error=str(e))
    except Exception as e:
        return AIResolutionDraftResponse(available=False, error=f"AI resolution generation failed: {str(e)}")


@router.post("/tickets/{ticket_id}/chat", response_model=AIChatResponse)
def chat_about_ticket(ticket_id: int, request: AIChatRequest, db: Session = Depends(get_db)):
    """Ticket-scoped conversational AI."""
    ai_service = get_ai_service()
    if not ai_service.is_available():
        return AIChatResponse(available=False, error="AI chat is unavailable. Please configure GROQ_API_KEY.")

    try:
        ticket_dict, comments_list, related = _get_ticket_context(db, ticket_id)
        answer = ai_service.chat_about_ticket(
            ticket=ticket_dict,
            comments=comments_list,
            related_tickets=related,
            history=request.history,
            question=request.question
        )
        return AIChatResponse(available=True, answer=answer)
    except ValueError as e:
        return AIChatResponse(available=False, error=str(e))
    except Exception as e:
        return AIChatResponse(available=False, error=f"AI chat failed: {str(e)}")


@router.post("/embeddings/rebuild")
def rebuild_embeddings(db: Session = Depends(get_db)):
    """Rebuild the semantic embedding index."""
    emb_service = get_embedding_service()
    if not emb_service.is_available():
        raise HTTPException(status_code=500, detail="Embedding service is unavailable.")
    
    try:
        count = emb_service.rebuild_index(db)
        return {"success": True, "embedded_tickets": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
