# BoredGames — AI Board Game Moderator

AI-powered board game moderator that learns rules, explains gameplay, adapts to house rules, and moderates live sessions — all powered by **Mistral La Plateforme**.

![License](https://img.shields.io/badge/license-MIT-blue)

## Features

| Feature | Description |
|---|---|
| **Game Search** | Search any board game by name — AI retrieves & structures complete rules |
| **OCR Rulebook Upload** | Upload rulebook photos/PDFs; Mistral OCR extracts rules automatically |
| **Interactive Explanations** | Quick Start, Step-by-Step, Simulated Playthrough, or free-form Q&A |
| **House Rule Engine** | Add custom rules with AI contradiction detection & balance analysis |
| **Live Moderation** | AI moderator tracks turns, validates moves, manages game flow in real time |
| **Dispute Resolution** | Neutral AI arbiter resolves rule disputes with official citations |
| **Voice Input** | Speak questions or actions; Voxtral transcribes in real time |

## AI Technology Stack

All AI capabilities use **Mistral La Plateforme** models:

- **`mistral-ocr-2512`** — Rulebook image OCR  
- **`mistral-large-2512`** — Game rules retrieval, web search, moderation agent, citation-backed dispute resolution  
- **`ft:mistral-small-3-2-2506:boredgames-*`** — Fine-tuned models for rule structuring, Q&A, and house rule validation  
- **`magistral-medium-2509`** — Playthrough simulation & novel reasoning  
- **`voxtral-mini-transcribe-2-2602`** — Voice input transcription  
- **`mistral-embed`** — Rulebook semantic search (RAG)  
- **`mistral-moderation-2411`** — Content safety  

## Architecture

```
frontend/          React 19 + TypeScript + Tailwind CSS (Vite)
backend/           FastAPI + SQLAlchemy + Mistral SDK
  ├── models/      Pydantic & SQLAlchemy models
  ├── routers/     REST API endpoints
  ├── services/    Mistral AI service layer
  └── websocket/   Real-time game session management
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- A [Mistral AI API key](https://console.mistral.ai/)

### 1. Clone & configure

```bash
git clone https://github.com/Mistral-AceOfSpades/BoredGames.git
cd BoredGames
cp .env.example .env
# Edit .env and set at minimum:
#   - MISTRAL_API_KEY=your_mistral_api_key
#   - SECRET_KEY=a long random string (do NOT leave the default placeholder)
# and any other required values for your environment.
```

### 2. Backend

```bash
python3.12 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Backend runs at `http://localhost:8000`. API docs at `/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` with hot reload. API calls are proxied to the backend.

### 4. Docker (optional)

```bash
docker compose up --build
```

Frontend at `http://localhost:3000`, backend at `http://localhost:8000`.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/games` | Search & structure a game by name |
| `GET` | `/api/games` | List all stored games |
| `GET` | `/api/games/:id` | Get game details |
| `POST` | `/api/ocr/upload` | OCR a rulebook image |
| `POST` | `/api/ocr/url` | OCR a rulebook from URL |
| `POST` | `/api/explain` | Generate explanation (quick_start / step_by_step / playthrough) |
| `POST` | `/api/explain/qa` | Q&A about game rules |
| `POST` | `/api/houserules/validate` | Validate a house rule |
| `POST` | `/api/houserules/add` | Add a validated house rule |
| `POST` | `/api/moderate/validate-move` | Validate a player move |
| `POST` | `/api/moderate/advance-turn` | Advance to next turn |
| `POST` | `/api/moderate/dispute` | Resolve a rule dispute |
| `POST` | `/api/voice/transcribe` | Transcribe audio input |
| `WS` | `/ws/:session_id` | Real-time game session WebSocket |

## Deployment

The frontend is deployed to **GitHub Pages** automatically on push to `main` via the CI workflow. The backend should be deployed separately (e.g., Railway, Fly.io, or any container host).

Set `VITE_API_URL` in the frontend build to point to your production backend URL.

## License

MIT — see [LICENSE](LICENSE) for details.
