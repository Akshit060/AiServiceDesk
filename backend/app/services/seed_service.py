"""
Seed service: idempotent, transactional import of HuggingFace dataset.

Checks ticket count for seed-completion (not just agents existence).
Entire import runs in a single transaction — partial imports roll back.
"""
import logging
import pandas as pd
from sqlalchemy.orm import Session
from app.models import Agent, Category, Ticket, Comment
from app.config import get_settings

logger = logging.getLogger(__name__)

STATUS_MAP = {
    "pending": "open",
    "in_progress": "in_progress",
    "resolved": "resolved",
    "closed": "resolved",
}


def is_seeded(db: Session) -> bool:
    """Check if the database has been fully seeded by verifying ticket count."""
    settings = get_settings()
    ticket_count = db.query(Ticket).count()
    return ticket_count >= settings.SEED_EXPECTED_TICKETS


def seed_database(db: Session) -> None:
    """
    Download and import the HuggingFace dataset into SQLite.
    Transactional: if any step fails, nothing is committed.
    """
    settings = get_settings()

    if is_seeded(db):
        logger.info("Database already seeded (%d+ tickets found). Skipping.", settings.SEED_EXPECTED_TICKETS)
        return

    logger.info("Starting database seed from HuggingFace dataset...")

    try:
        # Clear any partial data from a previous failed attempt
        db.query(Comment).delete()
        db.query(Ticket).delete()
        db.query(Category).delete()
        db.query(Agent).delete()
        db.flush()

        # ── Import Agents ──
        logger.info("Importing agents...")
        agents_df = pd.read_csv(settings.HF_AGENTS_CSV)
        for _, row in agents_df.iterrows():
            db.add(Agent(
                id=int(row["id"]),
                name=str(row["name"]),
                team=str(row["team"]),
            ))
        db.flush()
        logger.info("Imported %d agents.", len(agents_df))

        # ── Import Categories ──
        logger.info("Importing categories...")
        categories_df = pd.read_csv(settings.HF_CATEGORIES_CSV)
        for _, row in categories_df.iterrows():
            db.add(Category(
                id=int(row["id"]),
                name=str(row["name"]),
                service=str(row["service"]),
            ))
        db.flush()
        logger.info("Imported %d categories.", len(categories_df))

        # ── Import Tickets ──
        logger.info("Importing tickets...")
        tickets_df = pd.read_csv(settings.HF_TICKETS_CSV)
        for _, row in tickets_df.iterrows():
            original_status = str(row["status"])
            mapped_status = STATUS_MAP.get(original_status, "open")

            resolved_at = None
            if pd.notna(row.get("resolved_at")):
                try:
                    resolved_at = pd.to_datetime(row["resolved_at"])
                except Exception:
                    resolved_at = None

            first_response_at = None
            if pd.notna(row.get("first_response_at")):
                try:
                    first_response_at = pd.to_datetime(row["first_response_at"])
                except Exception:
                    first_response_at = None

            created_at = None
            if pd.notna(row.get("created_at")):
                try:
                    created_at = pd.to_datetime(row["created_at"])
                except Exception:
                    created_at = None

            db.add(Ticket(
                id=int(row["ticket_id"]),
                summary=str(row["summary"]) if pd.notna(row.get("summary")) else "No summary",
                description=str(row["description"]) if pd.notna(row.get("description")) else "No description",
                status=mapped_status,
                source_status=original_status,
                priority=str(row["priority"]) if pd.notna(row.get("priority")) else "P3",
                channel=str(row["channel"]) if pd.notna(row.get("channel")) else None,
                requester_department=str(row["requester_department"]) if pd.notna(row.get("requester_department")) else None,
                affected_service=str(row["affected_service"]) if pd.notna(row.get("affected_service")) else None,
                escalated=bool(row["escalated"]) if pd.notna(row.get("escalated")) else False,
                outage_related=bool(row["outage_related"]) if pd.notna(row.get("outage_related")) else False,
                category_id=int(row["category_id"]) if pd.notna(row.get("category_id")) else None,
                assigned_agent_id=int(row["assigned_agent_id"]) if pd.notna(row.get("assigned_agent_id")) else None,
                created_at=created_at,
                first_response_at=first_response_at,
                resolved_at=resolved_at,
            ))
        db.flush()
        logger.info("Imported %d tickets.", len(tickets_df))

        # ── Import Comments ──
        logger.info("Importing comments...")
        comments_df = pd.read_csv(settings.HF_COMMENTS_CSV)
        for _, row in comments_df.iterrows():
            comment_created_at = None
            if pd.notna(row.get("created_at")):
                try:
                    comment_created_at = pd.to_datetime(row["created_at"])
                except Exception:
                    comment_created_at = None

            db.add(Comment(
                id=int(row["comment_id"]),
                ticket_id=int(row["ticket_id"]),
                agent_id=int(row["agent_id"]) if pd.notna(row.get("agent_id")) else None,
                body=str(row["body"]) if pd.notna(row.get("body")) else "",
                visibility=str(row["visibility"]) if pd.notna(row.get("visibility")) else "public",
                team=str(row["team"]) if pd.notna(row.get("team")) else None,
                created_at=comment_created_at,
            ))
        db.flush()
        logger.info("Imported %d comments.", len(comments_df))

        # Commit the entire transaction
        db.commit()
        logger.info("Database seed completed successfully.")

    except Exception as e:
        db.rollback()
        logger.error("Database seed failed — transaction rolled back: %s", str(e))
        raise
