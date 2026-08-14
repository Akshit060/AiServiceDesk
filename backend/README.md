# Backend

The backend of the AI-Powered Engineer Service Desk is built with **FastAPI** and uses **SQLite** as its database.

## Architecture & Frameworks
- **Framework**: FastAPI
- **Database**: SQLite
- **ORM**: SQLAlchemy
- **Data Validation**: Pydantic
- **AI Integrations**: 
  - **LLM**: Groq API (model: `openai/gpt-oss-20b`) via the `groq` Python SDK.
  - **Embeddings**: Local Semantic Search using `sentence-transformers/all-MiniLM-L6-v2`.

## Semantic RAG (Retrieval-Augmented Generation)

### 1. Embeddings Engine (Sentence Transformers)
The application generates 384-dimensional dense vectors for resolved historical tickets. 
- During indexing, the `POST /api/embeddings/rebuild` endpoint scans all resolved tickets.
- It concatenates the ticket Summary, Description, and Resolution.
- It runs this text through the `all-MiniLM-L6-v2` model locally to generate a 384-d vector.
- The vectors are saved in the SQLite database inside the `ticket_embeddings` table as JSON arrays.

### 2. Semantic Retrieval
When a user views a ticket or asks the AI Copilot a question, the `retrieval_service` fetches historical evidence:
- It computes a new Query Vector for the current incident.
- It calculates the **cosine similarity** between the Query Vector and all stored historical vectors.
- It returns the most contextually relevant tickets to provide evidence grounding to the Groq LLM.

## AI Service (Groq Integration)
The `ai_service.py` handles communication with the Groq API.
The service is designed to be highly reliable, taking advantage of Groq's fast inference and strict JSON response formatting (`response_format={"type": "json_object"}`). 

The core features provided by the AI service are:
1. **Analyze Incident**: Structured root-cause analysis based on semantic evidence.
2. **Classify Ticket**: Automatic categorization and prioritization of new incidents.
3. **Generate Resolution Draft**: Formulates a resolution message by analyzing investigation notes and historical precedents.
4. **Ticket-Scoped Chat**: Context-aware Q&A based solely on incident history and retrieved evidence.

## Dataset Seeding
The backend includes an automatic seeding service (`seed_service.py`) that initializes the database using the `mindweave/help-desk-tickets` dataset from HuggingFace. Upon the first startup, it will populate the database with Agents, Categories, Tickets, and Comments.

## Environment Variables
The application is configured using a `.env` file at the root of the `backend/` directory.

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
DATABASE_URL=sqlite:///./servicedesk.db
```

*Note: The `GROQ_API_KEY` is backend-only and should never be exposed to the client application.*

## Important API Endpoints

- `GET /api/tickets`: List tickets
- `GET /api/tickets/{id}`: Get ticket details
- `POST /api/tickets/{id}/analyze`: Run the AI Incident Analysis
- `POST /api/tickets/classify`: Auto-classify a new ticket
- `POST /api/tickets/{id}/generate-resolution`: Draft a resolution
- `POST /api/tickets/{id}/ai/chat`: Ticket-scoped Copilot chat
- `POST /api/embeddings/rebuild`: Rebuild the semantic RAG index
- `GET /api/knowledge-base`: Browse historical tickets

## Running the Backend Locally

1. Create a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # source venv/bin/activate # Unix
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the `.env` file (ensure `GROQ_API_KEY` is set).
4. Run the Uvicorn server:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
