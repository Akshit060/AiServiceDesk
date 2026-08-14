import json
import logging
from groq import Groq
from typing import Optional, List, Dict, Any
from app.config import get_settings
from app.schemas import AIAnalysisResponse, AIClassifyResponse

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        settings = get_settings()
        self._api_key = settings.GROQ_API_KEY
        self._model_name = settings.GROQ_MODEL
        self._is_available = False
        self._client = None

        if self._api_key:
            try:
                self._client = Groq(api_key=self._api_key)
                self._is_available = True
            except Exception as e:
                logger.warning("Failed to configure Groq: %s", str(e))
                self._is_available = False

    def is_available(self) -> bool:
        return self._is_available

    def _call_groq(self, prompt: str, response_format: Optional[dict] = None) -> str:
        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": self._model_name,
            "messages": messages,
        }
        if response_format:
            kwargs["response_format"] = response_format
            
        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

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
            raise ValueError("AI analysis is currently unavailable. Please configure GROQ_API_KEY.")

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

        prompt = f"""You are an expert IT support engineer assistant. Analyze the incident and provide structured assistance.

## Current Incident
Title: {ticket.get('summary', '')}
Description: {ticket.get('description', '')}
Category: {ticket.get('category_name', 'Uncategorized')}
Priority: {ticket.get('priority', 'Unknown')}
Status: {ticket.get('status', 'Unknown')}

## Investigation Notes
{comments_text if comments_text else 'No investigation notes yet.'}

## Related Historical Incidents (Evidence)
{related_text if related_text else 'No related historical incidents found.'}

You MUST respond with valid JSON matching this exact structure:
{{
  "summary": "concise incident summary",
  "possible_cause": "likely root cause based on evidence",
  "investigation_steps": ["step 1", "step 2", "step 3"],
  "recommended_resolution": "suggested resolution based on incident and historical data",
  "confidence": "High/Medium/Low - honestly assess your confidence level",
  "suggested_category": "category name or null",
  "suggested_priority": "P1/P2/P3/P4 or null"
}}

Be practical and specific. Base recommendations on the historical support data provided.
If you lack evidence for a diagnosis, say so clearly. Do not fabricate certainty."""

        try:
            raw_content = self._call_groq(prompt, response_format={"type": "json_object"})
            if not raw_content:
                raise ValueError("AI returned an empty response.")

            parsed = json.loads(raw_content)
            validated = AIAnalysisResponse(**parsed)
            return validated
        except json.JSONDecodeError as e:
            logger.error("AI returned invalid JSON: %s", str(e))
            raise ValueError("AI returned a malformed response. Please try again.")
        except Exception as e:
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
            raise ValueError("AI classification is currently unavailable. Please configure GROQ_API_KEY.")

        categories_text = ", ".join(categories)
        prompt = f"""You are an IT support ticket classifier. Given a ticket title and description, suggest the most appropriate category and priority.

Available categories: {categories_text}
Available priorities: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)

Title: {summary}
Description: {description}

You MUST respond with valid JSON matching this exact structure:
{{
  "category": "exact category name from the available list",
  "priority": "P1, P2, P3, or P4",
  "summary": "brief one-line summary of the issue",
  "reasoning": "brief explanation of why you chose this category and priority",
  "confidence": "High/Medium/Low"
}}"""
        try:
            raw_content = self._call_groq(prompt, response_format={"type": "json_object"})
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

    def generate_resolution_draft(
        self,
        ticket: Dict[str, Any],
        comments: List[Dict[str, Any]],
        related_tickets: List[Dict[str, Any]],
    ) -> str:
        if not self.is_available():
            raise ValueError("AI resolution drafting is unavailable. Please configure GROQ_API_KEY.")

        comments_text = ""
        if comments:
            comments_text = "\n".join(
                f"- [{c.get('agent_name', 'Unknown')}]: {c.get('body', '')}" for c in comments
            )

        related_text = ""
        if related_tickets:
            entries = []
            for rt in related_tickets:
                if rt.get("resolution"):
                    entries.append(f"- Ticket #{rt.get('id')}: {rt.get('summary', '')}\n  Resolution: {rt['resolution']}")
            related_text = "\n".join(entries)

        prompt = f"""You are an expert IT support engineer assistant.
Generate a draft resolution message for the following ticket. The resolution message should be a professional, concise summary of what was done to fix the issue.
Use the investigation notes to understand what actions were taken. You may use related historical incidents for inspiration on standard wording, but do not invent actions that were not actually performed in this ticket's investigation notes.

## Current Incident
Title: {ticket.get('summary', '')}
Description: {ticket.get('description', '')}

## Investigation Notes
{comments_text if comments_text else 'No investigation notes yet.'}

## Related Historical Resolutions (Evidence)
{related_text if related_text else 'No related historical incidents found.'}

Output ONLY the raw text of the resolution draft. Do not include markdown formatting, introductory text, or JSON. Just the draft."""

        try:
            return self._call_groq(prompt, response_format=None).strip()
        except Exception as e:
            logger.error("AI resolution draft failed: %s", str(e))
            raise ValueError(f"AI generation failed: {str(e)}")

    def chat_about_ticket(
        self,
        ticket: Dict[str, Any],
        comments: List[Dict[str, Any]],
        related_tickets: List[Dict[str, Any]],
        history: List[dict],
        question: str,
    ) -> str:
        if not self.is_available():
            raise ValueError("AI chat is unavailable. Please configure GROQ_API_KEY.")

        comments_text = ""
        if comments:
            comments_text = "\n".join(
                f"- [{c.get('agent_name', 'Unknown')}]: {c.get('body', '')}" for c in comments
            )

        related_text = ""
        if related_tickets:
            entries = []
            for rt in related_tickets:
                entry = f"- Ticket #{rt.get('id')}: {rt.get('summary', '')}"
                if rt.get("resolution"):
                    entry += f"\n  Resolution: {rt['resolution']}"
                entries.append(entry)
            related_text = "\n".join(entries)
            
        history_text = ""
        if history:
            history_text = "\n".join(f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in history)

        prompt = f"""You are an IT support engineer assistant. Answer the engineer's question specifically regarding the current ticket and provided evidence.
Be concise and helpful. If the question cannot be answered from the incident or evidence, state that sufficient information is not available.
Do not invent facts or hallucinate.

## Current Incident Context
Title: {ticket.get('summary', '')}
Description: {ticket.get('description', '')}

## Investigation Notes
{comments_text if comments_text else 'None.'}

## Retrieved Historical Evidence
{related_text if related_text else 'None.'}

## Previous Chat History
{history_text if history_text else 'None.'}

Engineer's Question: {question}

Answer ONLY as a helpful assistant, directly answering the question."""

        try:
            return self._call_groq(prompt, response_format=None).strip()
        except Exception as e:
            logger.error("AI chat failed: %s", str(e))
            raise ValueError(f"AI chat failed: {str(e)}")


# Singleton instance
_ai_service: Optional[AIService] = None

def get_ai_service() -> AIService:
    global _ai_service
    # If the service isn't initialized or API key is missing (perhaps .env was updated), re-init it.
    if _ai_service is None or not _ai_service.is_available():
        _ai_service = AIService()
    return _ai_service
