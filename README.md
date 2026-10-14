# TravelLogix — Travel & Logistics in One Chat

TravelLogix is a modular full-stack enterprise platform that unifies Flights, Hotels, Trains, Buses, Maps, Weather, and Itinerary generation with complete Logistics operations (Shipment registration, Milestone tracking, Driver & Vehicle administration, and Telemetry verification).

---

## 1. System Architecture

```
                 ┌──────────────────────────────────────────┐
                 │           Chatbot (Web / API)            │
                 │              Next.js / React             │
                 │              localhost:3052              │
                 │        (chatbot/ - Customer Only)        │
                 └────────────────────┬─────────────────────┘
                                      │
                                      │ HTTPS / REST / SSE / WS
                                      ▼
                 ┌──────────────────────────────────────────┐
                 │           Chatbot (Web / API)            │
                 │              FastAPI Backend             │
                 │              localhost:5052              │
                 │       (backend/app/ - Unified API)       │
                 └────────────────────┬─────────────────────┘
                                      │
              ┌───────────────────────┼──────────────────────┐
              │                       │                      │
              ▼                       ▼                      ▼
        ┌───────────┐           ┌─────────────┐        ┌─────────────┐
        │PostgreSQL │           │    Redis    │        │ AI / RAG    │
        │   (DB)    │           │ (Cache/Bus) │        │ Orchestrator│
        └───────────┘           └─────────────┘        └──────┬──────┘
                                                              │
                               ┌──────────────────────────────┴──────────────┐
                               │                                             │
                               ▼                                             ▼
                         Tool Providers                               RAG Vector Store
                     (Flights, Trains, Buses,                       (Policies, FAQs,
                      Hotels, Weather, Maps,                         Packaging, Rules)
                      Shipment / Tracking)

                 ┌──────────────────────────────────────────┐
                 │      Chatbot Dashboard (Web / API)       │
                 │              Next.js / React             │
                 │              localhost:3053              │
                 │         (admin/ - Admin Only)            │
                 └────────────────────┬─────────────────────┘
                                      │
                                      │ HTTPS / REST / SSE / WS
                                      ▼
                 ┌──────────────────────────────────────────┐
                 │      Chatbot Dashboard (Web / API)       │
                 │              FastAPI Backend             │
                 │              localhost:5053              │
                 │       (backend/app/ - Unified API)       │
                 └──────────────────────────────────────────┘
```

---

## 2. Directory Structure

```
Travelogix/
├── chatbot/                      # Customer Frontend (Next.js, Port 3000)
│   ├── app/
│   │   ├── (auth)/               # Standalone Auth (/login, /register)
│   │   ├── (customer)/           # Customer Application (/ai-assistant, /logistics, ...)
│   │   └── layout.tsx            # Clean Root Layout (NO chatbot shell here)
│   ├── components/
│   ├── features/
│   ├── services/
│   ├── hooks/
│   ├── lib/
│   ├── types/
│   └── package.json
│
├── admin/                        # Admin Frontend (Next.js, Port 3001)
│   ├── app/
│   │   ├── (auth)/admin/login/   # Standalone Admin Login
│   │   ├── (admin)/admin/        # Protected Admin Dashboard & Management Routes
│   │   └── layout.tsx
│   ├── components/
│   ├── features/
│   ├── services/
│   ├── hooks/
│   ├── lib/
│   ├── types/
│   └── package.json
│
├── backend/                      # FastAPI Backend (Port 8000)
│   ├── app/
│   │   ├── main.py               # Application entrypoint & CORS
│   │   ├── api/v1/               # Modular REST endpoints
│   │   ├── core/                 # Config, security, exceptions, logging, dependencies
│   │   ├── db/                   # Async SQLAlchemy, session, base models
│   │   ├── models/               # Domain models
│   │   ├── schemas/              # Pydantic v2 schemas
│   │   ├── services/             # Domain business logic
│   │   ├── ai/                   # AI Orchestrator, tools, intent detection
│   │   ├── rag/                  # Document ingestion, vector store
│   │   ├── providers/            # Abstract travel & courier providers
│   │   ├── realtime/             # Redis pub/sub, SSE/WebSocket
│   │   └── utils/                # Tracking ID generator & helpers
│   ├── tests/                    # Pytest test suite
│   ├── requirements.txt
│   └── .env.example
│
├── shared/                       # Shared API contracts and types
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 3. Prerequisites

- **Python**: 3.10+ (tested up to Python 3.14)
- **Node.js**: v18+ or v20+
- **npm**: 9+ or 10+
- **Database**: SQLite (`travelogix.db` included locally, no setup needed)

---

## 4. Environment Variables

Copy the template to each backend if not present:

```bash
# Chatbot Backend (.env)
cd chatbot-backend

# Admin Backend (.env)
cd admin-backend
```

Key environment configurations:
- `DATABASE_URL`: `sqlite+aiosqlite:///../travelogix.db` for direct local development
- `PORT`: Chatbot backend (`5052`), Admin backend (`5053`)
- `CORS_ORIGINS`: Allowed origins (`http://localhost:3052` for Chatbot, `http://localhost:3053` for Admin)
- `ALLOWED_HOSTS`: Host header allow-list (`localhost,127.0.0.1`)
- `JWT_SECRET`, `CUSTOMER_SESSION_SECRET`, `ADMIN_SESSION_SECRET`: Session secrets for auth

---

## 5. Direct Local Development (No Docker Required)

### Launch All Services via Script

**PowerShell**:
```powershell
.\scripts\start-all.ps1
```

**Batch / Command Prompt**:
```cmd
.\start_all.bat
```

---

### Or Launch Services Individually

#### 1. Chatbot Backend (Port 5052)
```bash
cd chatbot-backend
python start_dev.py
```
Health Check: `http://localhost:5052/api/v1/health`

#### 2. Chatbot Frontend (Port 3052)
```bash
cd chatbot
npm run dev
```
Live at: `http://localhost:3052`

#### 3. Admin Backend (Port 5053)
```bash
cd admin-backend
python start_dev.py
```
Health Check: `http://localhost:5053/api/v1/health`

#### 4. Admin Frontend (Port 3053)
```bash
cd admin
npm run dev
```
Live at: `http://localhost:3053`

---

## 6. Verification & Tests

### Backend Tests
```bash
cd backend
pytest
```
The suite provisions its own throwaway database (`backend/.pytest-data/`, removed
when the session ends), so it never touches your development data. It verifies
health checks (`/health`, `/health/db`, `/health/redis`), CORS middleware,
centralized error handling, security utilities, the AI intent router, and the
authorisation rules (anonymous access to `/admin/*`, `/shipments*` and the admin
WebSocket channel must be refused).

### Frontend Typecheck & Build
```bash
cd chatbot && npm run build
cd admin && npm run build
```

---

## 7. Security & Anti-Hallucination Highlights

1. **Zero-Hallucination Policy**: current flight statuses, train running coordinates, bus ETAs and shipment GPS are never fabricated. A provider with no live backend returns the literal `"Data unavailable from the configured provider"`, and every demo/sample value is labelled as demo data (`provenance.is_mock` + a visible `DEMO DATA` marker). Nothing is invented to fill a gap — unknown destinations, missing shipment details and missing flight numbers all produce a clarifying question instead.
2. **Strict Layout Isolation**: `/login` and `/register` in `chatbot/` render ONLY authentication cards with zero chatbot or navigation elements mounted.
3. **RBAC & Ownership is enforced server-side.** Every `/api/v1/admin/*` route requires an authenticated administrator (the router itself carries a `require_admin` dependency, so a new endpoint cannot be added unguarded). Customer shipment and conversation endpoints resolve the owner from the session — a customer can only ever read their own shipments and transcripts. Administrator accounts are real, revocable database rows, and admin and customer tokens are signed with different secrets and carry a `typ` claim, so one family can never be replayed as the other.
4. **Sessions live in httpOnly cookies** (`secure` outside development, `SameSite=Lax`, lifetime bounded by the token TTL). JWTs are never returned in a response body and never stored in `localStorage`.
5. **Abuse controls**: login and registration are rate limited per client address (shared through Redis when available), passwords are bcrypt-hashed at cost 12 with a 72-byte guard, and registration failures are deliberately indistinguishable from a failed login so the endpoint is not a user-enumeration oracle.
6. **OAuth state is verified fail-closed** with a constant-time comparison, and only Google-verified email addresses may claim an account.
7. **The app refuses to start** in a non-development environment with placeholder secrets, `DEBUG=true`, `SQL_ECHO=true`, demo accounts enabled, a wildcard CORS origin, or identical admin/customer signing secrets.

