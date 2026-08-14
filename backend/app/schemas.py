from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Agent ───────────────────────────────────────────────

class AgentResponse(BaseModel):
    id: int
    name: str
    team: str

    model_config = {"from_attributes": True}


# ─── Category ────────────────────────────────────────────

class CategoryResponse(BaseModel):
    id: int
    name: str
    service: str

    model_config = {"from_attributes": True}


# ─── Comment ─────────────────────────────────────────────

class CommentCreate(BaseModel):
    agent_id: int
    body: str = Field(..., min_length=1, max_length=5000)
    visibility: str = "public"

class CommentResponse(BaseModel):
    id: int
    ticket_id: int
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    body: str
    visibility: str
    team: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Ticket ──────────────────────────────────────────────

VALID_STATUSES = ["open", "in_progress", "resolved"]
VALID_PRIORITIES = ["P1", "P2", "P3", "P4"]

class TicketCreate(BaseModel):
    summary: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=10000)
    priority: str = Field(default="P3")
    category_id: Optional[int] = None
    assigned_agent_id: Optional[int] = None

class TicketUpdate(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category_id: Optional[int] = None
    assigned_agent_id: Optional[int] = None
    resolution: Optional[str] = None

class TicketListItem(BaseModel):
    id: int
    summary: str
    status: str
    priority: str
    category_name: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class TicketResponse(BaseModel):
    id: int
    summary: str
    description: str
    status: str
    source_status: Optional[str] = None
    priority: str
    channel: Optional[str] = None
    requester_department: Optional[str] = None
    affected_service: Optional[str] = None
    escalated: bool = False
    outage_related: bool = False
    resolution: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    assigned_agent_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    first_response_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    comments: List[CommentResponse] = []

    model_config = {"from_attributes": True}

class TicketListResponse(BaseModel):
    tickets: List[TicketListItem]
    total: int
    page: int
    page_size: int


# ─── Dashboard ───────────────────────────────────────────

class StatusCount(BaseModel):
    status: str
    count: int

class PriorityCount(BaseModel):
    priority: str
    count: int

class CategoryCount(BaseModel):
    category: str
    count: int

class DashboardResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    unassigned_tickets: int
    critical_high_tickets: int  # P1 + P2
    by_status: List[StatusCount]
    by_priority: List[PriorityCount]
    by_category: List[CategoryCount]


# ─── AI ──────────────────────────────────────────────────

class AIAnalysisResponse(BaseModel):
    """Pydantic-validated AI analysis output."""
    summary: str = "No summary available."
    possible_cause: str = "Unable to determine cause."
    investigation_steps: List[str] = []
    recommended_resolution: str = "No recommendation available."
    confidence: str = "Low"
    suggested_category: Optional[str] = None
    suggested_priority: Optional[str] = None

class AIClassifyResponse(BaseModel):
    """Pydantic-validated AI classification output."""
    category: Optional[str] = None
    priority: Optional[str] = None
    summary: Optional[str] = None
    reasoning: Optional[str] = None
    confidence: Optional[str] = None

class AIErrorResponse(BaseModel):
    available: bool = False
    error: str = "AI analysis is currently unavailable."

class RelatedTicketResponse(BaseModel):
    id: int
    summary: str
    status: str
    priority: str
    category_name: Optional[str] = None
    resolution: Optional[str] = None
    relevance_score: Optional[float] = None

    model_config = {"from_attributes": True}


# ─── Knowledge Base ──────────────────────────────────────

class KnowledgeBaseEntry(BaseModel):
    ticket_id: int
    summary: str
    description: str
    category_name: Optional[str] = None
    resolution: Optional[str] = None
    comment_highlights: List[str] = []

    model_config = {"from_attributes": True}

class KnowledgeBaseResponse(BaseModel):
    entries: List[KnowledgeBaseEntry]
    total: int
