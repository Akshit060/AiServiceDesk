# AI-Powered Engineer Service Desk

## Project Overview
This is an **AI-Powered Engineer Service Desk** designed specifically for support engineers, not a customer-facing portal. It empowers support engineers to efficiently manage, investigate, and resolve incidents with the assistance of an AI Investigation Copilot.

The standard engineer workflow is:
```text
View incidents
→ Search/filter/prioritize
→ Take ownership
→ Investigate
→ Use AI assistance
→ Review historical support information
→ Add investigation comments
→ Record resolution
→ Resolve ticket
```

## Technology Stack
- **Frontend**: React + Vite
- **Routing**: React Router
- **Backend**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: SQLite
- **LLM Provider**: Groq
- **LLM Model**: `openai/gpt-oss-20b`
- **Local Embeddings**: Sentence Transformers
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Embedding Dimensions**: 384
- **Dataset**: `mindweave/help-desk-tickets`

## Dataset Documentation
The application relies on the `mindweave/help-desk-tickets` dataset, which includes approximately:
- 10 agents
- 8 categories
- 1,000 tickets
- 2,000 comments

Main source files used:
- `agents.csv`
- `categories.csv`
- `tickets.csv`
- `comments.csv`

The application introduces its own `resolution` field and preserves the original dataset status through `source_status`, while normalizing its active lifecycle status to:
- `open`
- `in_progress`
- `resolved`

## Stage 1 Functionality
Stage 1 successfully implemented the core service desk capabilities, satisfying 7/7 mandatory requirements:
- Ticket creation and persistence
- Ticket listing
- Search/filter/sort
- Ticket detail/investigation workbench
- Assignment
- Assign to Me
- Comments
- Resolution workflow
- Dashboard
- Historical incident retrieval
- Knowledge Base
- AI classification
- Basic AI incident analysis
- Validation/error handling
- Dataset seeding
- Engineer selector/context

## Commit 2 — AI Investigation Copilot
Commit 2 upgraded the original basic AI/retrieval functionality into a full semantic RAG-based investigation assistant.

**Architecture:**
```text
Current Ticket
      ↓
Local Embedding
      ↓
Semantic Retrieval
      ↓
Historical Evidence
      ↓
Groq LLM
      ↓
Structured AI Response
      ↓
Engineer Copilot
```

## Semantic Embedding Engine
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Vector size**: 384 dimensions
- **Storage**: Embeddings are stored in SQLite in the `ticket_embeddings` table.

**Indexing Process:**
The embedding rebuild process:
1. Reads resolved historical tickets.
2. Combines relevant ticket information such as Summary, Description, and Resolution.
3. Generates local embeddings.
4. Stores the vectors for reuse.

The manually tested rebuild endpoint (`POST /api/embeddings/rebuild`) successfully returned:
```json
{
  "success": true,
  "embedded_tickets": 900
}
```

## Semantic Retrieval
Retrieval uses **Cosine similarity** between the **Current ticket embedding** and **Historical ticket embeddings**. The system ranks historical incidents by semantic similarity and returns the most relevant historical incidents.

Manually tested Ticket #991 produced relevant results such as:
- #968 → 98%
- #587 → 96%
- #233 → 95%
- #421 → 93%
- #981 → 93%

*(Note: Similarity scores represent retrieval similarity, NOT AI confidence.)*

## Historical Evidence / Knowledge Base
The current Knowledge Base acts as a historical support knowledge repository built from old/resolved tickets (including ticket summary, description, category, resolution, and relevant comment highlights). Separate KB articles/SOP documents are not currently implemented as an independent RAG source.

The endpoint `GET /api/knowledge-base` was manually inspected and returned a total of 900 entries.

## Gemini → Groq Migration
The original Commit 2 implementation used Gemini, but the project was migrated to Groq because the Gemini API encountered restrictive quota/rate-limit errors during manual verification. 

The current LLM provider is **Groq** with the model **openai/gpt-oss-20b**. The API key is backend-only and configured through environment variables:
```env
GROQ_API_KEY=...
GROQ_MODEL=openai/gpt-oss-20b
DATABASE_URL=sqlite:///./servicedesk.db
```

## AI Investigation Copilot
### Analyze Incident
The Copilot provides structured information including Summary, Possible causes, Investigation steps, Recommended resolution, Confidence, and Suggestions/classification. 
Ticket #991 was manually tested successfully. The generated analysis included reasoning related to macOS Sonoma compatibility, VPN client update/rollback, and cache-related troubleshooting.

## Evidence Grounding
For Ticket #991, historical Ticket #587 contained evidence related to `macOS Sonoma` and historical Ticket #421 contained evidence related to `cache clear`. The AI analysis for #991 used these historical clues in its investigation recommendations.

Ticket #973's AI chat referenced historical Ticket #190, which was manually inspected and contained: `Found stale token in local credential manager.` Therefore, the ticket-scoped AI was successfully demonstrated to use historical evidence.

## AI-Generated Resolution Draft
The system supports generating a resolution draft, which was successfully tested on open Ticket #973. The generated output was a safe pending-status resolution message because the issue was still unresolved. 

*(Resolution draft generation was manually verified. The subsequent "Use Draft" population workflow was not included in the final verified test results.)*

## Ticket-Scoped AI Chat
Ticket-scoped AI chat was manually tested successfully. For Ticket #973, asking *"What should I check first for this issue based on historical evidence?"* resulted in a recommendation involving a stale/invalid credential token and referenced historical Ticket #190 (which contained `Found stale token in local credential manager.`). The chat demonstrated ticket-specific historical evidence usage.

## AI Classification
The `POST /api/tickets/classify` endpoint was manually tested successfully and returned:
```json
{
  "available": true,
  "classification": {
    "category": "Network & VPN",
    "priority": "P2",
    "summary": "VPN authentication failure after password change",
    "reasoning": "...",
    "confidence": "High"
  }
}
```
Structured/Pydantic validation remains in the AI pipeline.

## AI Failure Handling
An intentionally invalid Groq API key was used. The system returned a controlled error (`AI analysis failed: Error code: 401 - Invalid API Key`) and did not crash, demonstrating graceful handling of an AI authentication failure.

## API Endpoints
```text
GET    /api/dashboard

GET    /api/tickets
POST   /api/tickets

GET    /api/tickets/{ticket_id}
PATCH  /api/tickets/{ticket_id}

GET    /api/tickets/{ticket_id}/comments
POST   /api/tickets/{ticket_id}/comments

POST   /api/tickets/{ticket_id}/analyze
POST   /api/tickets/classify

POST   /api/tickets/{ticket_id}/ai/chat
POST   /api/tickets/{ticket_id}/generate-resolution

POST   /api/embeddings/rebuild

GET    /api/knowledge-base

GET    /api/agents
GET    /api/categories
```

## Configuration and Security
- API keys are backend-only.
- `.env` must not be committed.
- Groq API key must never be exposed to React.
- SQLite remains the database.
- No JWT/OAuth authentication was added in this stage.
- Engineer identity is currently handled through the existing engineer selector/context.

## Manual Verification Results
**Manual Verification**

Verified:
```text
✓ Backend startup
✓ Frontend startup
✓ FastAPI Swagger availability
✓ Ticket queue loading
✓ No critical browser console errors
✓ Embedding rebuild
✓ 900 historical ticket embeddings generated
✓ Semantic retrieval
✓ Historical incident similarity scores
✓ Historical ticket navigation
✓ AI incident analysis
✓ AI evidence grounding
✓ Resolution draft generation on an open ticket
✓ Ticket-scoped AI chat
✓ AI classification
✓ Invalid Groq API key failure handling
✓ Historical Knowledge Base endpoint inspection
```

Not verified:
```text
✗ Use Draft → Resolution field population
✗ Formal retrieval performance benchmark
✗ Separate KB/SOP RAG integration
```

## Known Limitations
1. The Knowledge Base is currently composed of old/resolved historical tickets rather than separate SOP/article documents.
2. The "Use Draft" resolution population workflow was not manually verified.
3. No formal retrieval precision/recall benchmark was performed.
4. No formal performance benchmark was performed for semantic retrieval.
5. AI responses depend on the availability and limits of the external Groq API.

## Developer/Setup Instructions
1. Clone repository
2. Create/activate backend virtual environment
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # source venv/bin/activate # Unix
   ```
3. Install backend dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Configure backend `.env`
   ```bash
   cp .env.example .env
   # Edit .env and add GROQ_API_KEY
   ```
5. Start FastAPI
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
6. Install frontend dependencies
   ```bash
   cd ../frontend
   npm install
   ```
7. Start Vite frontend
   ```bash
   npm run dev
   ```
8. Open the application at `http://localhost:5173`
