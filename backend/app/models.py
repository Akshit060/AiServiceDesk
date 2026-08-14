from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    team = Column(String(50), nullable=False)

    tickets = relationship("Ticket", back_populates="assigned_agent")
    comments = relationship("Comment", back_populates="agent")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    service = Column(String(50), nullable=False)

    tickets = relationship("Ticket", back_populates="category")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    summary = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="open")  # open, in_progress, resolved
    source_status = Column(String(20), nullable=True)  # original dataset status preserved
    priority = Column(String(5), nullable=False, default="P3")  # P1, P2, P3, P4
    channel = Column(String(20), nullable=True)
    requester_department = Column(String(100), nullable=True)
    affected_service = Column(String(100), nullable=True)
    escalated = Column(Boolean, default=False)
    outage_related = Column(Boolean, default=False)
    resolution = Column(Text, nullable=True)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    assigned_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    first_response_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    category = relationship("Category", back_populates="tickets")
    assigned_agent = relationship("Agent", back_populates="tickets")
    comments = relationship("Comment", back_populates="ticket", order_by="Comment.created_at")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    body = Column(Text, nullable=False)
    visibility = Column(String(20), default="public")
    team = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    ticket = relationship("Ticket", back_populates="comments")
    agent = relationship("Agent", back_populates="comments")


class TicketEmbedding(Base):
    __tablename__ = "ticket_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), unique=True, nullable=False)
    embedding = Column(Text, nullable=False)  # JSON serialized list of floats

    ticket = relationship("Ticket")
