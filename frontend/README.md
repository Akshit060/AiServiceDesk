# Frontend

The frontend of the AI-Powered Engineer Service Desk is built with **React** and **Vite**.

## Technology Stack
- **Framework**: React 18
- **Build Tool**: Vite
- **Routing**: React Router DOM
- **API Communication**: Fetch API (`src/services/api.js`)
- **Styling**: Vanilla CSS with CSS Variables

## Architecture & Features

### 1. Main Pages
- **Dashboard (`/`)**: Displays queue metrics, AI insights, and active assigned tickets.
- **Ticket Queue (`/tickets`)**: A comprehensive table view for browsing, filtering, sorting, and assigning incidents.
- **Ticket Investigation Workbench (`/tickets/:id`)**: The core engineering screen to view incident details, add investigation notes, manage status, and draft resolutions.
- **Knowledge Base (`/knowledge`)**: A historical view of resolved tickets that acts as the primary knowledge repository for semantic AI retrieval.

### 2. AI Investigation Copilot
The Ticket Investigation Workbench features a powerful AI Copilot panel powered by the Groq LLM and Semantic RAG.

- **Analyze Incident**: Triggers a comprehensive root-cause analysis based on historical ticket evidence, returning structured insights (Summary, Causes, Steps, Recommendations).
- **Resolution Draft UI**: Generates a professional resolution draft based on the ticket description and all subsequent investigation notes.
- **Ticket-Scoped Chat**: An interactive chat interface that answers questions contextually, heavily grounded in the specific incident and historical evidence.

### 3. Evidence Display
When investigating a ticket, the UI displays a **Related Historical Incidents** section below the Copilot. These incidents are dynamically fetched using the backend's semantic embedding engine and include a semantic similarity percentage score.

### 4. API Communication
All backend interactions are centralized in `src/services/api.js`. The frontend relies on the backend serving an API prefix at `/api/` (no versioning). The API Base URL is dynamically determined based on the current window origin (in production) or proxied during local development. 
*(Note: API Keys, including the Groq API Key, are handled securely on the backend and are never exposed to this React frontend).*

## Running the Frontend Locally

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
3. Open the application in your browser (typically `http://localhost:5173`).

*(Ensure the backend is running concurrently on port 8000 for full functionality).*
