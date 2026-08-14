# Democrance Insurance API — developer entrypoints.
#
# VENV defaults to an in-tree .venv so a reviewer's `make install` just works.
# Override it to keep the environment off a synced volume, e.g.:
#   make test VENV=$$HOME/.venvs/democrance-insurance-api

VENV ?= .venv
PY := $(VENV)/bin/python
RUFF := $(VENV)/bin/ruff
PYTEST := $(VENV)/bin/pytest

.DEFAULT_GOAL := help
.PHONY: help install run test lint format migrate makemigrations seed superuser up down demo

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Create the venv and install dev dependencies
	python3 -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements/dev.txt

run: ## Run the development server (SQLite fallback if no DATABASE_URL)
	$(PY) manage.py runserver

test: ## Run the full test suite with the coverage gate
	$(PYTEST)

lint: ## Lint with ruff
	$(RUFF) check .

format: ## Auto-format and auto-fix with ruff
	$(RUFF) format .
	$(RUFF) check --fix .

migrate: ## Apply database migrations
	$(PY) manage.py migrate

makemigrations: ## Create new migrations from model changes
	$(PY) manage.py makemigrations

seed: ## Seed demo users and sample data (available from Phase 9)
	$(PY) manage.py seed_demo

superuser: ## Create a Django superuser
	$(PY) manage.py createsuperuser

up: ## Start the Docker Compose stack (api + Postgres) — Phase 11
	docker compose up --build -d

down: ## Stop the Docker Compose stack
	docker compose down

demo: ## Seed then replay the seven diagram calls end to end — Phase 11
	$(PY) manage.py migrate
	$(PY) manage.py seed_demo
	$(PYTEST) tests/e2e -v
