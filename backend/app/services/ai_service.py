"""
AI service: OpenAI-compatible LLM integration with Pydantic validation.

All LLM responses are validated through Pydantic models before
being returned to the frontend. Malformed responses produce controlled errors.
"""
import json
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI
from app.config import get_settings
from app.schemas import AIAnalysisResponse, AIClassifyResponse

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        settings = get_settings()
        self._api_key = settings.OPENAI_API_KEY
        self._model = settings.OPENAI_MODEL
        self._client: Optional[OpenAI] = None

        if self._api_key:
            try:
                self._client = OpenAI(api_key=self._api_key)
            except Exception as e:
                logger.warning("Failed to initialize OpenAI client: %s", str(e))
                self._client = None

    def is_available(self) -> bool:
        return self._client is not None and bool(self._api_key)

    def analyze_ticket(
        self,
        ticket: Dict[str, Any],
        comments: List[Dict[str, Any]],
        related_tickets: List[Dict[str, Any]],
    ) -> AIAnalysisResponse:
        """
        Analyze a ticket with AI. Returns Pydantic-validated response.
        Raises ValueError with user-friendly message on any failure.
        """
        if not self.is_available():
            raise ValueError("AI analysis is currently unavailable. Please configure OPENAI_API_KEY.")

        # Build context
        comments_text = ""
        if comments:
            comments_text = "\n".join(
                f"- [{c.get('agent_name', 'Unknown')}]: {c.get('body', '')}" for c in comments
            )

        related_text = ""
        if related_tickets:
            entries = []
            for rt in related_tickets:
                entry = f"- Ticket #{rt.get('id')}: {rt.get('summary', '')} (Status: {rt.get('status', '')}, Priority: {rt.get('priority', '')})"
                if rt.get("resolution"):
                    entry += f"\n  Resolution: {rt['resolution']}"
                entries.append(entry)
            related_text = "\n".join(entries)

        system_prompt = """You are an expert IT support engineer assistant. Analyze the incident and provide structured assistance.

You MUST respond with valid JSON matching this exact structure:
{
  "summary": "concise incident summary",
  "possible_cause": "likely root cause based on evidence",
  "investigation_steps": ["step 1", "step 2", "step 3"],
  "recommended_resolution": "suggested resolution based on incident and historical data",
  "confidence": "High/Medium/Low - honestly assess your confidence level",
  "suggested_category": "category name or null",
  "suggested_priority": "P1/P2/P3/P4 or null"
}

Be practical and specific. Base recommendations on the historical support data provided.
If you lack evidence for a diagnosis, say so clearly. Do not fabricate certainty."""

        user_prompt = f"""## Current Incident
Title: {ticket.get('summary', '')}
Description: {ticket.get('description', '')}
Category: {ticket.get('category_name', 'Uncategorized')}
Priority: {ticket.get('priority', 'Unknown')}
Status: {ticket.get('status', 'Unknown')}

## Investigation Notes
{comments_text if comments_text else 'No investigation notes yet.'}

## Related Historical Incidents
{related_text if related_text else 'No related historical incidents found.'}

Provide your analysis as JSON."""

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                raise ValueError("AI returned an empty response.")

            # Parse and validate through Pydantic
            parsed = json.loads(raw_content)
            validated = AIAnalysisResponse(**parsed)
            return validated

        except json.JSONDecodeError as e:
            logger.error("AI returned invalid JSON: %s", str(e))
            raise ValueError("AI returned a malformed response. Please try again.")
        except Exception as e:
            if "json" in str(e).lower() or "validation" in str(e).lower():
                logger.error("AI response validation failed: %s", str(e))
                raise ValueError("AI returned an unexpected response format. Please try again.")
            logger.error("AI analysis failed: %s", str(e))
            raise ValueError(f"AI analysis failed: {str(e)}")

    def classify_ticket(
        self,
        summary: str,
        description: str,
        categories: List[str],
    ) -> AIClassifyResponse:
        """
        Classify a ticket with AI. Returns Pydantic-validated response.
        """
        if not self.is_available():
            raise ValueError("AI classification is currently unavailable. Please configure OPENAI_API_KEY.")

        categories_text = ", ".join(categories)

        system_prompt = f"""You are an IT support ticket classifier. Given a ticket title and description, suggest the most appropriate category and priority.

Available categories: {categories_text}
Available priorities: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)

You MUST respond with valid JSON matching this exact structure:
{{
  "category": "exact category name from the available list",
  "priority": "P1, P2, P3, or P4",
  "summary": "brief one-line summary of the issue",
  "reasoning": "brief explanation of why you chose this category and priority",
  "confidence": "High/Medium/Low"
}}"""

        user_prompt = f"""Title: {summary}
Description: {description}

Classify this ticket as JSON."""

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                raise ValueError("AI returned an empty response.")

            parsed = json.loads(raw_content)
            validated = AIClassifyResponse(**parsed)
            return validated

        except json.JSONDecodeError as e:
            logger.error("AI classification returned invalid JSON: %s", str(e))
            raise ValueError("AI returned a malformed response. Please try again.")
        except Exception as e:
            logger.error("AI classification failed: %s", str(e))
            raise ValueError(f"AI classification failed: {str(e)}")


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
