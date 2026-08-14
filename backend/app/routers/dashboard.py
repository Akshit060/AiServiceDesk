from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Ticket, Category
from app.schemas import DashboardResponse, StatusCount, PriorityCount, CategoryCount

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    """Returns aggregated dashboard metrics."""
    total = db.query(func.count(Ticket.id)).scalar() or 0
    open_count = db.query(func.count(Ticket.id)).filter(Ticket.status == "open").scalar() or 0
    in_progress = db.query(func.count(Ticket.id)).filter(Ticket.status == "in_progress").scalar() or 0
    resolved = db.query(func.count(Ticket.id)).filter(Ticket.status == "resolved").scalar() or 0
    unassigned = db.query(func.count(Ticket.id)).filter(Ticket.assigned_agent_id.is_(None)).scalar() or 0
    critical_high = db.query(func.count(Ticket.id)).filter(Ticket.priority.in_(["P1", "P2"])).scalar() or 0

    # By status
    by_status_rows = db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    by_status = [StatusCount(status=s, count=c) for s, c in by_status_rows]

    # By priority
    by_priority_rows = db.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
    by_priority = [PriorityCount(priority=p, count=c) for p, c in by_priority_rows]

    # By category
    by_category_rows = (
        db.query(Category.name, func.count(Ticket.id))
        .join(Category, Ticket.category_id == Category.id, isouter=True)
        .group_by(Category.name)
        .all()
    )
    by_category = [CategoryCount(category=cat or "Uncategorized", count=c) for cat, c in by_category_rows]

    return DashboardResponse(
        total_tickets=total,
        open_tickets=open_count,
        in_progress_tickets=in_progress,
        resolved_tickets=resolved,
        unassigned_tickets=unassigned,
        critical_high_tickets=critical_high,
        by_status=by_status,
        by_priority=by_priority,
        by_category=by_category,
    )
