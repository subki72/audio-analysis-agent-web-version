.PHONY: install test lint format run docker-build clean

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

lint:
	ruff check src tests web_api.py mcp_server.py

format:
	ruff format src tests web_api.py mcp_server.py

run:
	uvicorn web_api:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker build -t voicescript-api:latest .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
