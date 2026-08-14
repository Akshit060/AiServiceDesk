from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models import Ticket, Category, Agent, Comment
from app.schemas import (
    TicketCreate, TicketUpdate, TicketResponse, TicketListResponse,
    TicketListItem, CommentResponse, VALID_STATUSES, VALID_PRIORITIES,
)

router = APIRouter(prefix="/api", tags=["tickets"])


def _ticket_to_list_item(t: Ticket) -> TicketListItem:
    return TicketListItem(
        id=t.id,
        summary=t.summary,
        status=t.status,
        priority=t.priority,
        category_name=t.category.name if t.category else None,
        assigned_agent_name=t.assigned_agent.name if t.assigned_agent else None,
        created_at=t.created_at,
    )


def _ticket_to_response(t: Ticket) -> TicketResponse:
    comments = [
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
        for c in (t.comments or [])
    ]
    return TicketResponse(
        id=t.id,
        summary=t.summary,
        description=t.description,
        status=t.status,
        source_status=t.source_status,
        priority=t.priority,
        channel=t.channel,
        requester_department=t.requester_department,
        affected_service=t.affected_service,
        escalated=t.escalated or False,
        outage_related=t.outage_related or False,
        resolution=t.resolution,
        category_id=t.category_id,
        category_name=t.category.name if t.category else None,
        assigned_agent_id=t.assigned_agent_id,
        assigned_agent_name=t.assigned_agent.name if t.assigned_agent else None,
        created_at=t.created_at,
        updated_at=t.updated_at,
        first_response_at=t.first_response_at,
        resolved_at=t.resolved_at,
        comments=comments,
    )


@router.get("/tickets", response_model=TicketListResponse)
def list_tickets(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    agent_id: Optional[int] = Query(None),
    unassigned: Optional[bool] = Query(None),
    sort: Optional[str] = Query("newest"),  # newest, oldest, priority
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Ticket).options(
        joinedload(Ticket.category),
        joinedload(Ticket.assigned_agent),
    )

    # Filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Ticket.summary.ilike(search_term),
                Ticket.description.ilike(search_term),
            )
        )
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if category_id is not None:
        query = query.filter(Ticket.category_id == category_id)
    if agent_id is not None:
        query = query.filter(Ticket.assigned_agent_id == agent_id)
    if unassigned:
        query = query.filter(Ticket.assigned_agent_id.is_(None))

    # Total count before pagination
    total = query.count()

    # Sort
    if sort == "oldest":
        query = query.order_by(Ticket.created_at.asc())
    elif sort == "priority":
        query = query.order_by(Ticket.priority.asc(), Ticket.created_at.desc())
    else:  # newest (default)
        query = query.order_by(Ticket.created_at.desc())

    # Pagination
    offset = (page - 1) * page_size
    tickets = query.offset(offset).limit(page_size).all()

    return TicketListResponse(
        tickets=[_ticket_to_list_item(t) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/tickets", response_model=TicketResponse, status_code=201)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    if data.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Must be one of: {VALID_PRIORITIES}")

    if data.category_id is not None:
        cat = db.query(Category).filter(Category.id == data.category_id).first()
        if not cat:
            raise HTTPException(status_code=400, detail=f"Category ID {data.category_id} not found.")

    if data.assigned_agent_id is not None:
        agent = db.query(Agent).filter(Agent.id == data.assigned_agent_id).first()
        if not agent:
            raise HTTPException(status_code=400, detail=f"Agent ID {data.assigned_agent_id} not found.")

    ticket = Ticket(
        summary=data.summary,
        description=data.description,
        status="open",
        priority=data.priority,
        category_id=data.category_id,
        assigned_agent_id=data.assigned_agent_id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Re-query with joins
    ticket = (
        db.query(Ticket)
        .options(joinedload(Ticket.category), joinedload(Ticket.assigned_agent), joinedload(Ticket.comments))
        .filter(Ticket.id == ticket.id)
        .first()
    )
    return _ticket_to_response(ticket)


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
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
    return _ticket_to_response(ticket)


@router.patch("/tickets/{ticket_id}", response_model=TicketResponse)
def update_ticket(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")

    if data.status is not None:
        if data.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
        # Cannot resolve without resolution
        if data.status == "resolved" and not data.resolution and not ticket.resolution:
            raise HTTPException(status_code=400, detail="A resolution is required to resolve a ticket.")
        ticket.status = data.status
        if data.status == "resolved":
            ticket.resolved_at = datetime.now(timezone.utc)

    if data.priority is not None:
        if data.priority not in VALID_PRIORITIES:
            raise HTTPException(status_code=400, detail=f"Invalid priority. Must be one of: {VALID_PRIORITIES}")
        ticket.priority = data.priority

    if data.summary is not None:
        ticket.summary = data.summary

    if data.description is not None:
        ticket.description = data.description

    if data.category_id is not None:
        cat = db.query(Category).filter(Category.id == data.category_id).first()
        if not cat:
            raise HTTPException(status_code=400, detail=f"Category ID {data.category_id} not found.")
        ticket.category_id = data.category_id

    if data.assigned_agent_id is not None:
        agent = db.query(Agent).filter(Agent.id == data.assigned_agent_id).first()
        if not agent:
            raise HTTPException(status_code=400, detail=f"Agent ID {data.assigned_agent_id} not found.")
        ticket.assigned_agent_id = data.assigned_agent_id

    if data.resolution is not None:
        ticket.resolution = data.resolution

    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)

    # Re-query with joins
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
    return _ticket_to_response(ticket)
