import json
import logging
import math
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Ticket, TicketEmbedding
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def find_related_tickets(
    db: Session,
    ticket_id: int,
    summary: str,
    description: str,
    category_id: int | None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Find the most relevant historical tickets based on Semantic Embedding Similarity.
    """
    emb_service = get_embedding_service()
    if not emb_service.is_available():
        logger.warning("Embedding service not available. Skipping semantic retrieval.")
        return []

    # 1. Generate Query Embedding
    query_text = f"Title: {summary}\nDescription: {description}"
    try:
        query_emb = emb_service.get_embedding(query_text)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return []

    # 2. Load Stored Embeddings
    # In a production system with millions of rows, we'd use pgvector/Milvus.
    # For ~1000 tickets, in-memory cosine similarity is effectively instant.
    stored_embeddings = db.query(TicketEmbedding).all()
    if not stored_embeddings:
        return []

    # 3. Compute Similarities
    scored_candidates = []
    for stored in stored_embeddings:
        # Exclude the current ticket from historical results
        if stored.ticket_id == ticket_id:
            continue
            
        try:
            vec = json.loads(stored.embedding)
            sim = _cosine_similarity(query_emb, vec)
            
            # Hybrid boost: slight boost if they share the same category (if provided)
            # This requires joining or looking up the ticket, we can do it after fetching top N
            scored_candidates.append((stored.ticket_id, sim))
        except Exception as e:
            logger.error(f"Error computing similarity for ticket {stored.ticket_id}: {e}")

    # 4. Sort and take Top K
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    top_k_ids = [cid for cid, sim in scored_candidates[:limit]]
    
    if not top_k_ids:
        return []

    # 5. Fetch actual Ticket objects for the top K
    tickets = db.query(Ticket).filter(Ticket.id.in_(top_k_ids)).all()
    ticket_map = {t.id: t for t in tickets}

    results = []
    for cid, sim in scored_candidates[:limit]:
        candidate = ticket_map.get(cid)
        if not candidate:
            continue
            
        # Category match hybrid boost logic applied after fetching
        final_score = sim
        if category_id is not None and candidate.category_id == category_id:
            final_score += 0.05 # 5% absolute boost for exact category match

        # Get the most useful comment
        best_comment = None
        if candidate.comments:
            internal = [c for c in candidate.comments if c.visibility == "internal"]
            best_comment = (internal[-1] if internal else candidate.comments[-1]).body

        results.append({
            "id": candidate.id,
            "summary": candidate.summary,
            "status": candidate.status,
            "priority": candidate.priority,
            "category_name": candidate.category.name if candidate.category else None,
            "resolution": candidate.resolution or best_comment,
            "relevance_score": round(final_score, 4),
        })

    # Re-sort by final score in case hybrid boost changed the order
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results
