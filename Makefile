# Uso: make <target>

.PHONY: help install dev test lint format clean

# Default target
help:
	@echo "Gotinha"
	@echo ""
	@echo "Targets disponíveis:"
	@echo "  install     Instala dependências (uv sync)"
	@echo "  dev         Sobe servidor de desenvolvimento (uvicorn + reload)"
	@echo "  test        Roda testes (pytest)"
	@echo "  lint        Verifica código (ruff + mypy)"
	@echo "  format      Formata código (ruff format)"
	@echo "  clean       Remove caches e arquivos gerados"
	@echo ""

# Instalação
install:
	uv sync --dev

# Desenvolvimento
dev:
	uv run uvicorn gotinha.api.main:app --reload --host 0.0.0.0 --port 8000

# Testes
test:
	uv run pytest -v --tb=short

test-cov:
	uv run pytest --cov=gotinha --cov-report=term-missing --cov-report=html

# Linting & Formatação
lint:
	uv run ruff check .
	uv run mypy src/gotinha

format:
	uv run ruff format .
	uv run ruff check --fix .

# Limpeza
clean:
	rm -rf .ruff_cache .mypy_cache .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Verificação rápida antes de commit
pre-commit: lint test
	@echo "✓ Tudo ok para commit"