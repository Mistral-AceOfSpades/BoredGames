# Product Requirements Document (PRD)
Product Name: BoardGame BoredGames

## 0. AI Technology Stack (Mistral)
All AI capabilities are powered through **Mistral La Plateforme** API. The specific models are:

| Feature | Mistral Model | API Endpoint | Fine-tuned? |
|---|---|---|---|
| Rulebook image OCR & parsing | `mistral-ocr-2512` (OCR 3 v25.12) | `/v1/ocr` | No (specialist model) |
| Game rules retrieval & web search | `mistral-large-2512` (Mistral Large 3 v25.12) + built-in web search | `/v1/agents`, `/v1/conversations` | No (reasoning + tools) |
| Rule structuring & normalisation | **`ft:mistral-small-3-2-2506:boredgames-schema-v1`** (fine-tuned Mistral Small 3.2) | `/v1/chat/completions` | **Yes — replaces Large** |
| Interactive Q&A & rule explanation | **`ft:mistral-small-3-2-2506:boredgames-qa-v1`** (fine-tuned Mistral Small 3.2) | `/v1/chat/completions` | **Yes — replaces Medium** |
| Playthrough simulation & reasoning | `magistral-medium-2509` (Magistral Medium 1.2 v25.09) | `/v1/conversations` | No (novel reasoning) |
| Voice input transcription | `voxtral-mini-transcribe-2-2602` (Voxtral Mini Transcribe 2 v26.02) | `/v1/audio/transcriptions` | No (specialist model) |
| House rule contradiction detection | **`ft:mistral-small-3-2-2506:boredgames-houserules-v1`** (fine-tuned Mistral Small 3.2) | `/v1/chat/completions` | **Yes — replaces Medium** |
| Game moderation & state tracking | `mistral-large-2512` via Agents API + Function Calling | `/v1/agents`, `/v1/conversations` | No (agentic orchestration) |
| Dispute resolution with citations | `mistral-large-2512` with Citations feature | `/v1/conversations` | No (citation retrieval) |
| Rulebook semantic search (RAG) | `mistral-embed` (Mistral Embed v23.12) | `/v1/embeddings` | No (embedding model) |
| Content safety & moderation | `mistral-moderation-2411` (Mistral Moderation v24.11) | `/v1/moderations` | No (specialist model) |

> **Fine-tuning rationale**: Rule structuring, Q&A, and house rule contradiction detection are narrow, high-frequency, structured tasks over a fixed board game domain. Fine-tuning `mistral-small-3-2-2506` (6B-class) on curated domain data replaces `mistral-large-2512` and `magistral-medium-2509` for these paths, reducing per-call cost and latency by ~60–70% while improving domain accuracy. Large/reasoning models are retained only where web search orchestration, novel chain-of-thought, or citation retrieval is genuinely required.

## 1. Product Overview
BoardGame AI Moderator is an intelligent agent that can identify, learn, explain, adapt, and moderate board games. It enables players to quickly start and confidently play any board game by automatically retrieving rules (via image or name search), explaining gameplay interactively, incorporating house rules, and moderating live sessions.
The product is delivered as a **web application** — a static SPA hosted on **GitHub Pages** with a separate backend API — powered by **Mistral AI's La Plateforme** model suite.
The product reduces rulebook friction, resolves disputes, improves onboarding for new players, and enhances in-game flow.

## 2. Problem Statement
Board games frequently encounter the following issues:
Players struggle to interpret lengthy or ambiguous rulebooks.
House rules cause confusion or inconsistent gameplay.
Disputes arise due to unclear rule interpretations.
New players feel overwhelmed during onboarding.
Rule explanations are often passive rather than interactive.
There is currently no unified system that:
Extracts official rules directly from rulebook images.
Verifies house rules against base rules.
Dynamically moderates gameplay while adapting to live changes.

## 3. Objectives & Success Metrics
__Objectives__
Reduce game setup and rule-learning time.
Increase gameplay accuracy and consistency.
Support dynamic house rule integration.
Improve new player onboarding experience.
Provide neutral moderation during disputes.
__Key Metrics__
Average time to first playable round.
Rule accuracy rate (compared to official sources).
House rule validation success rate.
Player satisfaction score (post-game survey).
Dispute resolution turnaround time.
Retention rate across sessions.

## 4. Target Users
|Segment|Needs|
|---|---|
|Casual players|Fast rule explanation, easy onboarding|
|Experienced players|Accurate rulings, house rule integration|
|Game hosts|Neutral moderation and flow control|
|Board game cafés|Reliable rule support at scale|
|Families|Simplified explanations|

## 5. Core Features
### 5.1 Game Acquisition & Learning
__A. Find Game by Image__
- Upload photos of rulebook pages via web file picker or drag-and-drop.
- OCR extraction using **`mistral-ocr-2512` (OCR 3 v25.12)** via `/v1/ocr` — extracts interleaved text and images from multi-page documents at $2/1000 pages.
- Detect:
  - Setup instructions
  - Turn sequence
  - Win conditions
  - Special rules
- **`mistral-large-2512` (Mistral Large 3 v25.12)** with Structured Outputs normalises the extracted text into the game schema.
- Reconstruct structured game model.
__B. Find Game by Name__
- Input game title.
- **`mistral-large-2512`** Agent with the built-in **web search tool** retrieves rulebook content from verified online sources via `/v1/agents`.
- Cross-validate multiple sources using citation tracking.
- Normalize rules into structured schema via Structured Outputs (`response_format: json_schema`).
__Output__:
A standardized game model stored in the Document Library (built-in RAG connector):
- Components
- Player count
- Setup
- Turn structure
- Victory conditions
- Edge cases

### 5.2 Rule Explanation Engine
> **AI Model**: `magistral-medium-2509` (Magistral Medium 1.2 v25.09) — multimodal reasoning model via `/v1/conversations` with persistent conversation state.

__A. Interactive Explanation Modes__
1. Quick Start Mode
- 3–5 minute summary.
- Focus on:
  - Goal
  - Turn flow
  - Winning conditions.
2. Step-by-Step Mode
- Detailed walkthrough.
- Setup guidance.
- Component explanation.
3. Playthrough Simulation Mode
- **`magistral-medium-2509`** simulates 1 sample round with chain-of-thought reasoning to ensure rule consistency.
- Visual turn-by-turn narration rendered in the web UI.
- Persistent conversation state via `/v1/conversations` retains simulation context.
- After simulation:
  - "Would you like to continue the simulation or start your own game?"
4. Q&A Mode
- **Voice input**: transcribed in real time by **`voxtral-mini-transcribe-2-2602` (Voxtral Mini Transcribe 2 v26.02)** via browser MediaRecorder API streaming to `/v1/audio/transcriptions`.
- Text input processed by **`magistral-medium-2509`** with context from the active game's Document Library.
- Context-aware answers with **Citations** feature referencing exact rulebook passages.
- Conflict detection via Structured Outputs:
  - "Official rule states X. Your house rule modifies this."

### 5.3 House Rule Adaptation System
> **AI Models**:
> - Contradiction analysis: `magistral-medium-2509` (Magistral Medium 1.2 v25.09) with Structured Outputs.
> - Voice input: `voxtral-mini-transcribe-2-2602` (Voxtral Mini Transcribe 2 v26.02).

__A. Pre-Game House Rule Integration__
- User inputs modifications via web form or voice.
- **`magistral-medium-2509`** with Structured Outputs (`response_format: json_schema`) performs:
  - Comparison with the base rule retrieved from the Document Library.
  - Flags contradictions with specific rule citations.
  - Highlights impacted mechanics.
  - Simulates consequences using chain-of-thought reasoning.
__B. Verification & Testing__
- Logical consistency checks powered by **`magistral-medium-2509`** reasoning:
  - Infinite loops?
  - Unwinnable states?
  - Broken economy?
- Provide structured impact summary (returned as JSON):
  - Balance impact
  - Length impact
  - Complexity impact
__C. In-Game Dynamic Rule Listening__
- **`voxtral-mini-transcribe-2-2602`** streams live audio via browser MediaRecorder API for real-time rule change detection.
- **`mistral-large-2512`** Agent detects intent and confirms:
  - "You're adding a new rule: X. Confirm?"
- Updates game state model via Function Calling tools.
- Adjusts moderation logic through the persistent Conversation state.

### 5.4 Game Moderation Engine
> **AI Models**:
> - Core moderation agent: `mistral-large-2512` (Mistral Large 3 v25.12) via Agents & Conversations API.
> - Dispute resolution: `mistral-large-2512` with Citations feature.
> - Content safety: `mistral-moderation-2411` (Mistral Moderation v24.11).

__A. Turn Management__
- **`mistral-large-2512`** Agent with Function Calling tools maintains and updates the turn state machine.
- Track player turns via persistent Conversation state across `/v1/conversations`.
- Remind next player via web UI notifications.
- Enforce phase order using custom function tools (`advance_turn`, `check_phase`).
__B. Rule Enforcement__
- Detect illegal moves via voice declaration (transcribed by **`voxtral-mini-transcribe-2-2602`**) or text input.
- **`mistral-large-2512`** cross-references the Document Library built-in connector for the relevant rule.
- Prompt clarification with rule citation:
  - "That move appears invalid under Rule 3.2. Proceed anyway?"
__C. Dispute Resolution__
- **`mistral-large-2512`** with **Citations** feature provides verifiable rule citations pointing to exact rulebook passages.
- Offer interpretation hierarchy:
  - Official rule (from Document Library RAG)
  - FAQ clarifications
  - Community consensus
  - House rule override
- User-submitted dispute text screened by **`mistral-moderation-2411`** before processing.
__D. Game State Tracking (Optional Advanced Mode)__
- Custom Function Calling tools (`update_score`, `track_resource`, `check_win_condition`) called by the **`mistral-large-2512`** Agent.
- Track:
  - Scores
  - Resources
  - Cards
  - Win triggers
- Predict:
  - Imminent victory conditions
  - Illegal states

## 6. User Experience Flow
__Scenario 1: Starting a New Game__
1. User enters game name.
2. System retrieves rulebook.
3. User selects “Quick Start.”
4. System explains.
5. User adds house rule.
6. System verifies.
7. Game begins.
8. AI moderates and answers questions live.
__Scenario 2: Unknown Game via Image__
1. User uploads rulebook images.
2. System extracts structure.
3. Displays parsed rule summary.
4. User confirms correctness.
5. Explanation begins.

## 7. Technical Architecture

### 7.A Deployment & Hosting
| Concern | Technology | Notes |
|---|---|---|
| **Frontend hosting** | **GitHub Pages** | Static SPA served from the `gh-pages` branch of the `BoredGames` repo. Custom domain via CNAME. Free HTTPS. |
| **Frontend framework** | React 19 + Vite 6 (TypeScript) | Static build (`vite build`) outputs to `dist/`; deployed via `gh-pages` npm package or GitHub Actions. |
| **Styling** | Tailwind CSS | Utility-first; purged at build time for minimal bundle. |
| **Client-side routing** | React Router v7 (hash mode) | Hash-based routing (`/#/game`, `/#/explain`) avoids GitHub Pages 404 on page refresh. |

### 7.B Backend Systems
GitHub Pages is static-only, so all server-side logic lives in a **separate backend API** and supporting services:

| System | Technology | Purpose |
|---|---|---|
| **API server** | Python 3.12 + FastAPI, deployed on **Railway** (or Render) | Proxies all Mistral La Plateforme calls; owns business logic, session management, and game state mutations. Exposes REST + WebSocket endpoints. |
| **Mistral AI proxy** | FastAPI route handlers calling `mistral` Python SDK | All `/v1/ocr`, `/v1/chat/completions`, `/v1/agents`, `/v1/conversations`, `/v1/audio/transcriptions`, `/v1/embeddings`, `/v1/moderations` calls are server-side only — API keys never reach the client. |
| **Database** | PostgreSQL 16 (Railway managed) | Persistent storage for user accounts, saved game schemas, house rule sets, session history, and fine-tuning training data exports. |
| **Cache / real-time state** | Redis 7 (Upstash serverless) | Ephemeral game session state, turn tracking, conversation ID mapping, and rate-limiting counters. |
| **Auth** | OAuth 2.0 via GitHub (passport / authlib) + JWT | GitHub OAuth aligns with the GitHub Pages ecosystem; JWT tokens authenticate API calls from the SPA. |
| **File / blob storage** | Cloudflare R2 (S3-compatible) | Uploaded rulebook images stored temporarily for OCR processing; auto-expired after 24 h unless user opts in to retain. |
| **Background jobs** | Celery + Redis broker (on Railway) | Async processing for: OCR pipeline on large rulebooks, fine-tuning dataset assembly, and benchmark evaluation runs. |
| **WebSocket** | FastAPI WebSocket endpoints | Real-time moderation events, turn notifications, and voice transcription streaming pushed to the SPA. |
| **CI/CD** | GitHub Actions | Frontend: build + deploy to `gh-pages` branch on push to `main`. Backend: Docker build + deploy to Railway on push to `main`. |
| **Monitoring** | Sentry (errors) + Axiom (logs + traces) | Backend error tracking and structured logging; Mistral API latency traces. |

#### Architecture Diagram
```
┌─────────────────────────────────────────────┐
│               GitHub Pages                  │
│   Static React SPA (Vite build)             │
│   /#/game  /#/explain  /#/moderate          │
└──────────────┬──────────────────────────────┘
               │ HTTPS REST + WebSocket
               ▼
┌─────────────────────────────────────────────┐
│         FastAPI Backend (Railway)            │
│  ┌────────────┐  ┌───────────┐  ┌────────┐  │
│  │ Auth (JWT) │  │ Game API  │  │ WS Hub │  │
│  └────────────┘  └─────┬─────┘  └───┬────┘  │
│                        │            │        │
│  ┌─────────────────────▼────────────▼─────┐  │
│  │        Mistral SDK Proxy Layer         │  │
│  │  OCR · Chat · Agents · Embed · Mod    │  │
│  └────────────────────────────────────────┘  │
└──────┬──────────┬──────────┬────────────────┘
       │          │          │
       ▼          ▼          ▼
  PostgreSQL    Redis     Cloudflare R2
  (Railway)   (Upstash)  (blob storage)
```

### 7.B Mistral AI Processing Pipeline
```
Rulebook Image  →  mistral-ocr-2512 (/v1/ocr)
                        ↓
               Raw text + image blocks
                        ↓
          mistral-large-2512 + Structured Outputs
                        ↓
              Normalised Game Schema (JSON)
                        ↓
        Document Library (built-in RAG connector)
```

```
User Query (text/voice)
    ↓ (voice) voxtral-mini-transcribe-2-2602
    ↓
 magistral-medium-2509 + Document Library
    ↓
    Answer with Citations + Conflict Flags
```

```
Live Game Session
    ↓
 mistral-large-2512 Agent (/v1/conversations)
  ├─ Function Calling tools: turn engine, score tracker
  ├─ Built-in web search: cross-reference rulings
  ├─ Document Library: current game rulebook
  └─ mistral-moderation-2411: user input safety
```

### 7.C Knowledge Base
- **Document Library** (Mistral built-in RAG connector): indexed game rulebooks and FAQs — embedded via `mistral-embed` (Mistral Embed v23.12)
- Structured game templates stored as JSON in the Document Library
- Community rulings appended as versioned documents

### 7.D Multimodal Input
| Input | Model / Mechanism |
|---|---|
| Text | Direct to Mistral chat/agents endpoints |
| Voice | `voxtral-mini-transcribe-2-2602` real-time transcription |
| Rulebook image upload | `mistral-ocr-2512` document extraction |
| Web rulebook URL | `mistral-large-2512` agent + built-in web search |
| Camera (Phase 2) | `mistral-medium-3-1-2508` (Mistral Medium 3.1 v25.08) vision input |

### 7.E Fine-Tuning Strategy

#### Models to Fine-tune
| Fine-tune Job | Base Model | Target Task | Training Signal |
|---|---|---|---|
| `boredgames-schema-v1` | `mistral-small-3-2-2506` | OCR text → structured JSON game schema | 2 000+ (raw OCR text, normalised schema JSON) pairs from top 200 games |
| `boredgames-qa-v1` | `mistral-small-3-2-2506` | Rulebook Q&A with rule citations | 5 000+ (question, rulebook context, cited answer) triples |
| `boredgames-houserules-v1` | `mistral-small-3-2-2506` | House rule contradiction detection | 3 000+ (base rule, proposed house rule, contradiction label + reason) triples |

#### Training Data Requirements
- **Schema normalisation** (`boredgames-schema-v1`):
  - Source: OCR output from `mistral-ocr-2512` run against physical rulebooks of the top 200 games.
  - Label: Manually verified JSON game schema per game (components, setup, turns, win conditions, edge cases).
  - Format: Mistral fine-tuning JSONL — `{"messages": [{"role": "user", "content": "<ocr_text>"}, {"role": "assistant", "content": "<json_schema>"}]}`.
  - Volume: ≥2 000 examples; target ≥10 examples per game genre.
- **Q&A** (`boredgames-qa-v1`):
  - Source: Community rule FAQs, BoardGameGeek forum answers, official publisher errata.
  - Label: Answer string + exact rule section reference.
  - Format: System prompt sets the game context; user message is the question; assistant message is the cited answer.
  - Volume: ≥5 000 QA pairs across ≥50 games.
- **House rules** (`boredgames-houserules-v1`):
  - Source: Synthetic contradictions generated from base rules + crowdsourced house rule submissions.
  - Label: `{"contradiction": true/false, "reason": "...", "impacted_rules": [...]}`.
  - Format: Structured Outputs with `json_schema` response format.
  - Volume: ≥3 000 pairs with balanced positive/negative contradiction ratio.

#### Fine-tuning Pipeline (Mistral La Plateforme)
```
1. Prepare JSONL datasets → upload via POST /v1/files
2. Create fine-tuning job → POST /v1/fine_tuning/jobs
   { "model": "mistral-small-3-2-2506",
     "training_files": ["<file_id>"],
     "hyperparameters": { "epochs": 3, "learning_rate": 1e-5 } }
3. Poll job status → GET /v1/fine_tuning/jobs/{job_id}
4. Deploy fine-tuned model → referenced as ft:<org>/<suffix>
5. Run benchmark suite (see §7.F) — promote to production only if thresholds met
6. Retrain trigger: accuracy drops >3% over 7-day rolling window
```

#### Model Size & Cost Rationale
- `mistral-small-3-2-2506` is a 22B-class instruction model; fine-tuned on narrow domain data it matches or exceeds the accuracy of `mistral-large-2512` on in-domain tasks at ~70% lower token cost and ~50% lower latency.
- `magistral-medium-2509` is retained **only** for playthrough simulation and novel dispute reasoning where chain-of-thought over unseen rules is needed — not for routine domain tasks.
- Estimated token cost reduction from fine-tuning: ~65% on schema normalisation calls and ~55% on Q&A calls.

### 7.F Benchmarking & Evaluation

#### Benchmark Datasets
| Dataset | Purpose | Size | Refresh Cadence |
|---|---|---|---|
| `bg-schema-eval` | Schema normalisation accuracy vs gold standard | 200 held-out games | Quarterly |
| `bg-qa-eval` | Q&A answer correctness + citation accuracy | 500 QA pairs | Monthly |
| `bg-houserule-eval` | Contradiction detection F1 | 300 labelled pairs | Monthly |
| `bg-latency-eval` | End-to-end p50/p95 latency per user scenario | 100 synthetic sessions | Every release |
| `bg-cost-eval` | Tokens per session for schema + Q&A paths | 50 representative sessions | Every release |

#### Metrics & Acceptance Thresholds
| Metric | Target | Blocking? |
|---|---|---|
| Schema field accuracy (exact match per field) | ≥95% | Yes |
| Q&A answer correctness (human eval or LLM-as-judge) | ≥92% | Yes |
| Rule citation precision | ≥90% | Yes |
| Contradiction detection F1 | ≥0.88 | Yes |
| OCR structured extraction accuracy | ≥93% | Yes |
| Q&A response latency p95 | <2 s | Yes |
| OCR pipeline latency p95 | <5 s | No (alerting only) |
| Tokens per Q&A session (fine-tuned vs base) | ≤40% of base model cost | Yes |

#### Evaluation Approach
- **Automated**: LLM-as-judge using `mistral-large-2512` to score Q&A correctness and citation accuracy against gold answers. Schema fields validated by JSON schema validator.
- **Human eval panel**: 5 board game domain experts review 50 randomly sampled outputs per release for subjective quality, edge case handling, and house rule reasoning.
- **Regression suite**: All metrics re-run on every fine-tune job before promotion; a job is blocked if any _blocking_ threshold is missed.
- **A/B shadow testing**: Fine-tuned model runs in shadow mode for 48 h in staging before production cut-over; production traffic p95 latency monitored.
- **Drift detection**: Weekly automated run of `bg-schema-eval` and `bg-qa-eval` against the live model; >3% accuracy drop triggers a retraining ticket.

## 8. Non-Functional Requirements
|Category|Requirement|
|---|---|
|Accuracy|≥95% schema field accuracy; ≥92% Q&A correctness; ≥0.88 F1 on contradiction detection (see §7.F thresholds)|
|Latency|<2s p95 for Q&A (fine-tuned Small 3.2); <5s p95 for OCR pipeline|
|Privacy|No image retention unless consent (Cloudflare R2 auto-expiry 24 h); Mistral API data-handling terms apply|
|Scalability|Support 1M+ games indexed via Document Library; Railway autoscaling for backend; GitHub Pages CDN for frontend|
|Platform|Web-first; static SPA on **GitHub Pages** with responsive design for desktop and mobile browsers|
|Hosting|Frontend on GitHub Pages (free tier); Backend on Railway (starter or pro plan); Redis on Upstash (serverless); Blob storage on Cloudflare R2|
|Offline Mode|Cache downloaded rulebooks and game schemas in localStorage/IndexedDB; service worker for offline SPA shell|
|API Cost|OCR: $2/1000 pages; fine-tuned Small 3.2 calls ≤40% of base Large cost; embeddings via `mistral-embed`|
|Model Versioning|Fine-tuned model versions pinned in backend env vars; rollback to previous version within 15 min via Railway env update|
|Retraining Trigger|Automated retraining ticket raised if any benchmark metric drops >3% over 7-day rolling window|

## 9. Risks & Mitigation
|Risk|Mitigation|
|---|---|
|OCR errors|Multi-pass validation & user confirmation|
|Incorrect rule interpretation|Fine-tuned schema model + cross-source verification; weekly drift detection|
|Complex games with heavy edge cases|Tiered support: fine-tuned Small 3.2 for known games, fallback to `magistral-medium-2509` for unknown/complex games|
|Ambiguous house rules|Structured confirmation prompts; fine-tuned contradiction model with explicit reasoning output|
|Legal/IP concerns|Link to official sources, do not redistribute full copyrighted content|
|Fine-tune data quality|Human expert review of ≥10% of training labels before each fine-tune job submission|
|Fine-tuned model regression|Blocking benchmark suite (§7.F) gates every promotion; automatic rollback via pinned model version|
|Training data staleness|Quarterly refresh of `bg-schema-eval` and `bg-qa-eval` datasets with newly released games|

## 10. Future Enhancements
- AR camera-based board recognition using **`mistral-medium-3-1-2508` (Mistral Medium 3.1 v25.08)** multimodal vision.
- Real-time card recognition via live camera stream.
- Strategy coaching mode powered by **`magistral-medium-2509`** extended reasoning.
- Integration with digital board game platforms via Mistral Agents Handoff API.
- Player behavior analytics with **`mistral-embed`** for pattern clustering.
- Tournament mode with multi-agent orchestration (Handoffs across game moderator agents).
- Mobile app (React Native) reusing the same FastAPI backend.

## 11. Competitive Landscape
|Competitor|Limitation|
|---|---|
|Static rulebook apps|No dynamic moderation|
|Video tutorials|Not interactive|
|Forums|Not real-time|
|Digital board games|Not adaptable to physical games|

This product differentiates through dynamic learning + adaptive moderation + live house rule integration.

## 12. MVP Scope
__Included:__
- Static React SPA hosted on **GitHub Pages** (Vite build, hash routing)
- FastAPI backend deployed on **Railway** (Python 3.12)
- PostgreSQL (Railway) for persistent data; Redis (Upstash) for session state; Cloudflare R2 for image uploads
- GitHub OAuth for authentication
- Game search by name using `mistral-large-2512` + built-in web search
- Rulebook image upload + OCR via `mistral-ocr-2512`
- Structured rule extraction + normalisation via `mistral-large-2512` Structured Outputs
- Interactive Q&A explanation via `magistral-medium-2509` + Document Library RAG
- Voice input via `voxtral-mini-transcribe-2-2602`
- Manual house rule input + contradiction validation via `magistral-medium-2509`
- Basic turn moderation via `mistral-large-2512` Agents + Function Calling
- Content safety screening via `mistral-moderation-2411`
- CI/CD via GitHub Actions (frontend → `gh-pages` branch; backend → Railway Docker deploy)
__Excluded (Phase 2):__
- AR board tracking (`mistral-medium-3-1-2508` vision)
- Automatic illegal move detection via camera
- Strategy optimization
- Mobile native app

## 13. Launch Strategy
__Phase 1:__
- Focus on top 200 most popular board games.
- Target board game cafés and university clubs.
__Phase 2:__
- Expand to community-uploaded rulebooks.
- Enable API for digital platforms.

## 14. Definition of Done
- 90% of beta users complete a game without external rule consultation.
- House rule adaptation works without breaking base mechanics.
- Disputes reduced by >50% compared to baseline.
- System handles at least 50 complex board games accurately.

## Summary
BoredGames is an intelligent board game companion that:
- Learns games via image or search.
- Explains interactively.
- Adapts to house rules.
- Moderates gameplay in real time.
- Resolves disputes neutrally.

It transforms rule-heavy board games into smooth, guided, adaptive experiences while preserving player flexibility and creativity.

