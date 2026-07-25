.PHONY: setup start stop test eval clean docker-start docker-stop

setup:
	@echo "Setting up project..."
	@bash setup.sh

start:
	@echo "Starting application..."
	@bash start.sh

stop:
	@echo "Stopping application..."
	@bash stop.sh

test:
	@echo "Running tests..."
	@bash run-tests.sh

eval:
	@echo "Running RAG retrieval & grounding eval..."
	@cd backend && $$( [ -x venv/bin/python ] && echo venv/bin/python || echo python3 ) -m eval.run_eval

clean:
	@echo "Cleaning up..."
	@rm -rf backend/venv
	@rm -rf backend/__pycache__
	@rm -rf backend/**/__pycache__
	@rm -rf frontend/node_modules
	@rm -rf frontend/dist
	@rm -rf data/documents/*
	@rm -rf data/vectorstore/*
	@rm -rf data/logs/*
	@echo "Cleanup complete!"

docker-start:
	@echo "Starting with Docker..."
	@bash start-docker.sh

docker-stop:
	@echo "Stopping Docker containers..."
	@docker-compose down

install:
	@echo "Installing dependencies..."
	@cd backend && pip install -r requirements.txt
	@cd frontend && npm install