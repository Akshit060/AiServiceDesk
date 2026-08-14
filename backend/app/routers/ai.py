from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app.models import Ticket, Category, Comment
from app.schemas import AIAnalysisResponse, AIClassifyResponse, AIErrorResponse, RelatedTicketResponse
from app.services.ai_service import get_ai_service
from app.services.retrieval_service import find_related_tickets

router = APIRouter(prefix="/api", tags=["ai"])


class ClassifyRequest(BaseModel):
    summary: str
    description: str


@router.post("/tickets/{ticket_id}/analyze")
def analyze_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """AI-powered ticket analysis with historical context."""
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

    ai_service = get_ai_service()
    if not ai_service.is_available():
        return AIErrorResponse(available=False, error="AI analysis is currently unavailable. Please configure OPENAI_API_KEY.")

    try:
        # Get related historical tickets
        related = find_related_tickets(
            db=db,
            ticket_id=ticket.id,
            summary=ticket.summary,
            description=ticket.description,
            category_id=ticket.category_id,
        )

        # Build context dicts
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
        return AIErrorResponse(available=False, error="AI classification is currently unavailable. Please configure OPENAI_API_KEY.")

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
    """Get related historical tickets without AI analysis."""
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
