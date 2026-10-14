# TravelLogix Backend (`backend/`)

Unified FastAPI backend supporting AI-powered Travel and Logistics orchestration, PostgreSQL relational models, Redis real-time bus, and abstract provider integrations.

## Key Features
- **FastAPI 0.115+** with asynchronous SQLAlchemy 2.x and Pydantic v2.
- **Real-Time Health Probes**: `/health`, `/health/db`, and `/health/redis` report actual service states (never fabricating connectivity).
- **Strict Anti-Hallucination**: Live flight, train, bus, and shipment telemetry checks require verified provider or database data.
- **Strict CORS**: Allow-origins configured for `http://localhost:3000` (Customer) and `http://localhost:3001` (Admin).
- **Centralized Error Handling**: Standardized error payloads (`{ "success": false, "error": { "code": "...", "message": "..." } }`).

## Answer Pipeline (travel chat)

Every travel request is resolved in a fixed order, and the tier that produced the reply is
reported in `provenance.mode`:

| Tier | Source | When it answers | `provenance.mode` |
| --- | --- | --- | --- |
| 1 | Local JSON dataset (`app/data/*.json`) | the route/city has rows | `json` |
| 2 | LLM (Groq / Gemini / OpenRouter) | dataset has nothing for that route/city | `llm` |
| 3 | RAG knowledge base (`app/rag/service.py`) | the question is about TravelLogix itself (policies, services) | `rag` |

Rules enforced by that order:

* **A dataset hit never reaches a model.** The rows are rendered deterministically, so a
  model can neither reword them nor invent a number that is not in the file.
* **Tier 2 is labelled.** Any answer that stands in for a dataset miss is prefixed with
  `_Not in my local dataset — general guidance only:_`.
* **Tier 2 may not confirm a service.** If the model claims a route "is available" when we
  hold no rows for it, the claim is discarded and an honest "not in my dataset" answer is
  returned instead.
* **Status lookups are dataset-only.** An unknown flight/train/bus number reports that it is
  not in the dataset rather than describing a position that cannot be verified.
* **Answers are short.** At most 4 one-line options per answer, no trailing provenance
  footer. `LLM` answers are capped by the system prompt (`app/ai/providers/llm.py`).

### JSON datasets

| File | Contents | Regenerate with |
| --- | --- | --- |
| `app/data/flights.json` | 673 flights on 256 directed routes, 32 cities | `python scripts/generate_travel_json.py` |
| `app/data/hotels.json` | 225 hotels across 40 city keys (aliases included) | same |
| `app/data/trains.json` | 840 trains on 340 directed routes + 170 running statuses | same |
| `app/data/buses.json` | 438 buses on 178 directed routes + 219 running statuses | same |
| `app/data/weather.json` | 45 city keys of seasonal climate reference | same |

The generator is deterministic (fixed seeds), so re-running it produces byte-identical files.
Values are plausible reference data for offline/demo mode and are surfaced to the customer as
"based on available travel data" — the datasets are not live inventory.

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
Runs at `http://localhost:5052`.

## Running Tests
```bash
pytest
```
