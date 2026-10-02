.PHONY: setup start stop test eval clean docker-start docker-stop

setup:
	cd backend && python3 -m venv venv && venv/bin/pip install --upgrade pip && venv/bin/pip install -r requirements.txt
	backend/venv/bin/python -m spacy download en_core_web_lg
	cd frontend && npm install
	@[ -f backend/.env ] || { cp .env.example backend/.env; echo "Now set GEMINI_API_KEY in backend/.env"; }

# Backend and frontend together; Ctrl+C stops both.
start:
	@[ -f backend/.env ] || { echo "backend/.env not found. Run 'make setup' first."; exit 1; }
	@trap 'kill 0' INT TERM; \
	(cd backend && venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000 --reload) & \
	(cd frontend && npm run dev) & \
	wait

# Only the listening servers: a plain port match would also kill browsers connected to them.
stop:
	-lsof -t -iTCP:8000 -iTCP:5173 -sTCP:LISTEN | xargs kill

test:
	cd backend && venv/bin/python -m pytest

eval:
	cd backend && venv/bin/python -m eval.run_eval

clean:
	rm -rf backend/venv frontend/node_modules frontend/dist
	find backend -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf data/documents/* data/vectorstore/* data/logs/*

docker-start:
	@[ -f .env ] || { cp .env.example .env; echo "Set GEMINI_API_KEY in .env, then rerun."; exit 1; }
	docker compose up -d

docker-stop:
	docker compose down
