# AI Scientist OS

AI Scientist OS is a production-style hackathon application that turns a scientific hypothesis into a structured, evidence-backed experiment planning workspace.

It is designed to feel like a blend of a lab notebook, an agentic research assistant, and a project workspace rather than a simple chatbot.

## What It Does

- Parses a hypothesis into structured scientific fields
- Runs a deterministic workflow with typed intermediate outputs
- Uses local Ollama models through the OpenAI Python SDK compatibility layer
- Searches PubMed through NCBI E-utilities without requiring an API key
- Searches the web and Semantic Scholar pages through SerpAPI when configured
- Looks up compounds through PubChem PUG REST
- Persists projects, sources, plans, workflow state, and exports
- Produces literature-backed experiment plans with citations
- Applies safety guardrails before, during, and after generation
- Estimates costs from a curated local price table
- Builds timelines and exportable PDF, DOCX, and CSV outputs

## Stack

### Frontend

- Next.js 16
- TypeScript
- Tailwind CSS
- TanStack Query
- React Hook Form
- Zod
- Zustand
- Recharts
- React Flow
- Markdown rendering for evidence summaries

### Backend

- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- pgvector
- Redis
- RQ background jobs
- httpx
- tenacity
- structlog
- OpenAI Python SDK configured for Ollama

### Infrastructure

- Docker Compose
- `pgvector/pgvector:pg16`
- Redis 7
- Local Docker volume storage for exports and generated artifacts

## Repository Layout

```text
backend/
  app/
    api/routes/
    core/
    data/seed/
    db/
    schemas/
    services/
    tests/
frontend/
  app/
  components/
  lib/
scripts/
docker-compose.yml
Makefile
.env.example
```

## Local Model Setup

This project does not use OpenAI hosted models.

It uses the OpenAI Python SDK against Ollama's OpenAI-compatible API:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)
```

Preferred models:

- Chat and planning: `gpt-oss:120b-cloud`
- Chat fallback: `deepseek-v3.1:671b-cloud`
- Lower-latency cloud alternative: `gpt-oss:20b-cloud`
- Embeddings: no Ollama cloud embedding model is configured by default; the app uses keyword retrieval fallback unless you explicitly add a local embedding model later.

Pull models manually if needed:

```bash
ollama signin
ollama pull gpt-oss:120b-cloud
ollama pull deepseek-v3.1:671b-cloud
```

You can also run:

```bash
backend/.venv/Scripts/python scripts/setup_ollama.py
```

That helper:

- checks whether Ollama is installed
- checks whether Ollama is reachable
- attempts to start `ollama serve` if possible
- verifies a supported cloud chat model is available
- avoids requiring a local embedding model by default

## Prerequisites

- Python 3.12
- Node.js 22+ or recent Node 20+
- npm
- Ollama
- Docker Desktop if you want the Compose stack
- PostgreSQL and Redis locally, or the Docker Compose services

## Environment

Copy `.env.example` to `.env` and set the values you need.

Important variables:

- `DATABASE_URL`
- `ASYNC_DATABASE_URL`
- `REDIS_URL`
- `LOCAL_STORAGE_PATH`
- `SERPAPI_API_KEY`
- `NCBI_EMAIL` optional but recommended
- `NCBI_API_KEY` optional
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `OLLAMA_CHAT_MODEL`
- `NEXT_PUBLIC_BACKEND_URL`

## Run It

### Recommended flow

1. Copy `.env.example` to `.env`
2. Start infrastructure
3. Set up Ollama and models
4. Install backend and frontend dependencies
5. Start the API, worker, and frontend

### Infrastructure

```bash
docker compose up postgres redis
```

The backend stores generated files on a Docker-managed local volume mounted at `/app/storage`
inside the container, while export metadata remains in PostgreSQL via the `export_artifacts`
table.

For local backend development on Windows, the Docker Postgres service is published on
`localhost:5433` to avoid conflicts with an already installed local PostgreSQL service.

If you run the backend in Docker, note that Ollama should be reached via:

- `http://host.docker.internal:11434`

That mapping, plus the local storage volume mount, is already documented in
`docker-compose.yml`.

### One-time setup

```bash
make setup
```

If `make` is not available on Windows, use the equivalent commands:

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python -m pip install --upgrade pip
backend/.venv/Scripts/pip install -e backend[dev]
npm --prefix frontend install
backend/.venv/Scripts/python scripts/setup_ollama.py
```

### Development

```bash
make dev
```

On Windows, `make dev` now starts the Docker dependencies, backend, worker, and frontend
from a single terminal through [scripts/dev.py](D:/FAST/Hackathon/scripts/dev.py).

You can also run it directly:

```powershell
backend/.venv/Scripts/python scripts/dev.py
```

### URLs

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)
- Deep health: [http://localhost:8000/health/deep](http://localhost:8000/health/deep)

## Workflow Pipeline

The orchestrator is deterministic and step-based:

1. Safety pre-check
2. Hypothesis parser
3. Query planner
4. Literature retrieval
5. Protocol retrieval
6. Chemical retrieval
7. Source ranking
8. RAG context building
9. Experiment plan generation
10. Safety review
11. Cost estimation
12. Timeline estimation
13. Critique
14. Final persistence

Each step stores state in `workflow_runs` and `workflow_steps`.

## API Surface

Implemented endpoints:

- `GET /health`
- `GET /health/deep`
- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `POST /projects/{project_id}/run`
- `GET /projects/{project_id}/status`
- `GET /projects/{project_id}/sources`
- `GET /projects/{project_id}/plan`
- `PATCH /projects/{project_id}/plan`
- `POST /projects/{project_id}/refine`
- `POST /projects/{project_id}/exports/pdf`
- `POST /projects/{project_id}/exports/docx`
- `POST /projects/{project_id}/exports/csv`
- `GET /projects/{project_id}/exports/{artifact_id}`

## Safety Boundaries

The system refuses or constrains dangerous requests.

Blocked or restricted areas include:

- harmful pathogens
- unknown environmental microbe culturing
- harmful genetic engineering
- toxins
- explosives
- controlled substances
- human or animal experimentation
- clinical or diagnostic use
- self-experimentation

Allowed educational domains currently center on:

- plant growth experiments
- enzyme activity experiments
- safe educational microbiology overviews
- safe educational PCR planning
- cell culture overview only
- general chemistry safety lookup

## Testing And Checks

Run the full local check set:

```bash
make test
make lint
```

Equivalent direct commands:

```powershell
backend/.venv/Scripts/python -m pytest backend/app/tests
backend/.venv/Scripts/python -m ruff check backend/app
backend/.venv/Scripts/python -m mypy backend/app
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

## Current Seed Examples

- Does caffeine affect plant growth?
- Does light color affect seed germination?
- Does salt concentration affect plant growth?
- How does temperature affect enzyme activity?
- Does pH affect catalase activity?

## Troubleshooting

### Ollama is not reachable

Use:

```bash
ollama serve
ollama list
```

Then rerun:

```bash
backend/.venv/Scripts/python scripts/setup_ollama.py
```

### Deep health shows missing chat model

Either pull the configured model:

```bash
ollama signin
ollama pull gpt-oss:120b-cloud
```

or switch `OLLAMA_CHAT_MODEL` in `.env` to another installed cloud model such as
`deepseek-v3.1:671b-cloud` or `gpt-oss:20b-cloud`.

### SerpAPI is not configured

The app still works with:

- PubMed
- PubChem
- curated fallback seed data

but web and Semantic Scholar URL search will be limited.

### Postgres or Redis health is failing

Make sure Docker Desktop is running, then:

```bash
docker compose up postgres redis
```

If you already have local services, confirm the credentials in `.env`.

## Known Limitations

- Deep health will report a missing configured chat model until an Ollama cloud model such as `gpt-oss:120b-cloud` or `deepseek-v3.1:671b-cloud` is available in your local Ollama library.
- PDF export currently uses ReportLab for portability rather than a browser-rendered layout engine.
- Vector embeddings are scaffolded for pgvector persistence, but the default cloud-only setup uses keyword ranking because no Ollama cloud embedding model is configured by default.
- The refinement flow is deterministic and rule-based for reliability; it does not yet use a separate full LLM critique-refine pass.
- The current seed datasets are intentionally small and only act as a fallback.
- Storage is intentionally local-only: Docker volume plus PostgreSQL metadata, with no cloud
  file backend.

## Next Improvements

- Add authenticated users and project ownership
- Add versioned experiment plans with diff history
- Add richer pgvector similarity search using stored embeddings end-to-end
- Add editable citations and manual source selection
- Add richer PDF styling with browser-based rendering
- Add source-specific extraction policies and more protocol templates
- Add rate limiting middleware and auth-ready JWT flows
