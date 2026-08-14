from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Comment, Ticket, Agent
from app.schemas import CommentCreate, CommentResponse
from typing import List

router = APIRouter(prefix="/api", tags=["comments"])


@router.get("/tickets/{ticket_id}/comments", response_model=List[CommentResponse])
def list_comments(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")

    comments = (
        db.query(Comment)
        .filter(Comment.ticket_id == ticket_id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    return [
        CommentResponse(
            id=c.id,
            ticket_id=c.ticket_id,
            agent_id=c.agent_id,
            agent_name=c.agent.name if c.agent else None,
            body=c.body,
            visibility=c.visibility,
            team=c.team,
            created_at=c.created_at,
        )
        for c in comments
    ]


@router.post("/tickets/{ticket_id}/comments", response_model=CommentResponse, status_code=201)
def add_comment(ticket_id: int, data: CommentCreate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")

    agent = db.query(Agent).filter(Agent.id == data.agent_id).first()
    if not agent:
        raise HTTPException(status_code=400, detail=f"Agent ID {data.agent_id} not found.")

    comment = Comment(
        ticket_id=ticket_id,
        agent_id=data.agent_id,
        body=data.body,
        visibility=data.visibility,
        team=agent.team,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return CommentResponse(
        id=comment.id,
        ticket_id=comment.ticket_id,
        agent_id=comment.agent_id,
        agent_name=agent.name,
        body=comment.body,
        visibility=comment.visibility,
        team=comment.team,
        created_at=comment.created_at,
    )
