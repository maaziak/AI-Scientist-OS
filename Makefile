PYTHON ?= py -3.12
PIP := backend/.venv/Scripts/pip
PY := backend/.venv/Scripts/python
NPM := npm --prefix frontend

.PHONY: setup dev backend frontend worker db-migrate test lint health docker-up docker-down

setup:
	$(PYTHON) -m venv backend/.venv
	$(PY) -m pip install --upgrade pip
	$(PIP) install -e backend[dev]
	$(NPM) install
	$(PY) scripts/setup_ollama.py

dev:
	backend/.venv/Scripts/python scripts/dev.py

backend:
	backend/.venv/Scripts/python -m uvicorn app.main:app --reload --app-dir backend

frontend:
	$(NPM) run dev

worker:
	backend/.venv/Scripts/python scripts/run_worker.py

db-migrate:
	cd backend && ../backend/.venv/Scripts/alembic upgrade head

test:
	$(PY) -m pytest backend/app/tests
	$(NPM) run lint
	$(NPM) run typecheck

lint:
	$(PY) -m ruff check backend/app
	$(PY) -m mypy backend/app
	$(NPM) run lint
	$(NPM) run typecheck

health:
	curl http://localhost:8000/health/deep

docker-up:
	docker compose up --build

docker-down:
	docker compose down
