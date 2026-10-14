# TravelLogix Backend (`backend/`)

Unified FastAPI backend supporting AI-powered Travel and Logistics orchestration, PostgreSQL relational models, Redis real-time bus, and abstract provider integrations.

## Key Features
- **FastAPI 0.115+** with asynchronous SQLAlchemy 2.x and Pydantic v2.
- **Real-Time Health Probes**: `/health`, `/health/db`, and `/health/redis` report actual service states (never fabricating connectivity).
- **Strict Anti-Hallucination**: Live flight, train, bus, and shipment telemetry checks require verified provider or database data.
- **Strict CORS**: Allow-origins configured for `http://localhost:3000` (Customer) and `http://localhost:3001` (Admin).
- **Centralized Error Handling**: Standardized error payloads (`{ "success": false, "error": { "code": "...", "message": "..." } }`).

## Environment Setup
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

## Running the Server
```bash
python start_dev.py
```
Runs at `http://localhost:5053`.

## Running Tests
```bash
pytest
```
