import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Ticket, TicketEmbedding

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self._model = None
        self._model_name = "sentence-transformers/all-MiniLM-L6-v2"

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model {self._model_name}...")
                self._model = SentenceTransformer(self._model_name)
                logger.info("Embedding model loaded.")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self._model = None
        return self._model

    def is_available(self) -> bool:
        return self._load_model() is not None

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        model = self._load_model()
        if not model:
            raise ValueError("Embedding model is not available.")
        
        # sentence-transformers returns a numpy array, convert to list of floats
        embedding = model.encode(text)
        return embedding.tolist()

    def rebuild_index(self, db: Session) -> int:
        """
        Rebuilds the entire embedding index for resolved tickets.
        Only embeds useful textual information.
        """
        if not self.is_available():
            raise ValueError("Cannot rebuild index: embedding model unavailable.")

        logger.info("Starting embedding index rebuild...")

        # Fetch all resolved tickets
        tickets = db.query(Ticket).filter(Ticket.status == "resolved").all()
        
        if not tickets:
            logger.info("No resolved tickets found to embed.")
            return 0

        # Clear existing embeddings
        db.query(TicketEmbedding).delete()
        db.commit()

        count = 0
        embeddings_to_insert = []
        for ticket in tickets:
            # Create a meaningful representation of the incident
            category_name = ticket.category.name if ticket.category else "Uncategorized"
            affected_service = ticket.affected_service or "Unknown"
            resolution = ticket.resolution or "No explicit resolution recorded."
            
            text_to_embed = f"Title: {ticket.summary}\nDescription: {ticket.description}\nCategory: {category_name}\nAffected Service: {affected_service}\nResolution: {resolution}"
            
            try:
                emb_vector = self.get_embedding(text_to_embed)
                emb_record = TicketEmbedding(
                    ticket_id=ticket.id,
                    embedding=json.dumps(emb_vector)
                )
                embeddings_to_insert.append(emb_record)
                count += 1
            except Exception as e:
                logger.error(f"Failed to embed ticket {ticket.id}: {e}")

        if embeddings_to_insert:
            db.bulk_save_objects(embeddings_to_insert)
            db.commit()

        logger.info(f"Embedding index rebuild complete. {count} tickets embedded.")
        return count

# Singleton instance
_embedding_service: Optional[EmbeddingService] = None

def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
