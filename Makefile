.PHONY: install run test lint format docker-build docker-run demo

install:
	pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload

test:
	python -m pytest -v

lint:
	ruff check .

format:
	ruff check --fix . && ruff format .

docker-build:
	docker build -t stride-threat-modeling .

docker-run:
	docker compose up --build

demo:
	python scripts/gerar_diagrama_exemplo.py
	python scripts/analisar_lote.py images --saida docs/exemplos
