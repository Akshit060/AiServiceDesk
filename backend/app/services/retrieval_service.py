"""
Retrieval service: lightweight text-based search for relevant historical tickets.

Uses keyword/token overlap + category matching to score relevance.
Intentionally simple for Stage 1, extensible to vector search later.
"""
import re
import logging
from typing import List, Dict, Any
from collections import Counter
from sqlalchemy.orm import Session
from app.models import Ticket, Comment

logger = logging.getLogger(__name__)

# Common stop words to exclude from matching
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "because", "but", "and",
    "or", "if", "while", "that", "this", "it", "its", "up", "about",
    "which", "what", "who", "whom", "their", "they", "them", "we", "us",
    "our", "your", "you", "he", "she", "him", "her", "his", "my", "me",
    "i", "reported", "user", "issue", "problem", "please", "help",
}


def _tokenize(text: str) -> List[str]:
    """Extract meaningful tokens from text."""
    if not text:
        return []
    text = text.lower()
    tokens = re.findall(r'\b[a-z]{2,}\b', text)
    return [t for t in tokens if t not in STOP_WORDS]


def _compute_score(query_tokens: Counter, candidate_tokens: Counter, category_match: bool) -> float:
    """Compute relevance score between query and candidate."""
    if not query_tokens or not candidate_tokens:
        return 0.0

    # Intersection of token sets
    common = set(query_tokens.keys()) & set(candidate_tokens.keys())
    if not common:
        return 0.0

    # Score = sum of min(query_count, candidate_count) for shared tokens
    overlap_score = sum(min(query_tokens[t], candidate_tokens[t]) for t in common)

    # Normalize by query size
    normalized = overlap_score / max(sum(query_tokens.values()), 1)

    # Category match bonus (50% boost)
    if category_match:
        normalized *= 1.5

    return round(normalized, 4)


def find_related_tickets(
    db: Session,
    ticket_id: int,
    summary: str,
    description: str,
    category_id: int | None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Find the most relevant historical tickets based on text similarity.
    Returns up to `limit` tickets with their resolutions and comments.
    """
    query_text = f"{summary} {description}"
    query_tokens = Counter(_tokenize(query_text))

    if not query_tokens:
        return []

    # Fetch resolved/closed tickets (excluding the current ticket)
    candidates = (
        db.query(Ticket)
        .filter(Ticket.id != ticket_id)
        .filter(Ticket.status == "resolved")
        .limit(500)  # Performance guard: score at most 500 candidates
        .all()
    )

    scored = []
    for candidate in candidates:
        candidate_text = f"{candidate.summary} {candidate.description}"
        candidate_tokens = Counter(_tokenize(candidate_text))
        category_match = (category_id is not None and candidate.category_id == category_id)
        score = _compute_score(query_tokens, candidate_tokens, category_match)

        if score > 0:
            # Get the most useful comment (last internal note or any comment)
            best_comment = None
            if candidate.comments:
                internal = [c for c in candidate.comments if c.visibility == "internal"]
                best_comment = (internal[-1] if internal else candidate.comments[-1]).body

            scored.append({
                "id": candidate.id,
                "summary": candidate.summary,
                "status": candidate.status,
                "priority": candidate.priority,
                "category_name": candidate.category.name if candidate.category else None,
                "resolution": candidate.resolution or best_comment,
                "relevance_score": score,
            })

    # Sort by score descending, take top N
    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored[:limit]
