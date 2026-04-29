# Task Management API

Flask REST API for tasks with JWT authentication, PostgreSQL, SQLAlchemy, and Alembic migrations.

## Tech Stack

- Python 3.12
- Flask + `flask-restx`
- SQLAlchemy + Alembic
- PostgreSQL
- JWT access tokens (`flask-jwt-extended`)
- `uv` for dependency management
- `pytest` for tests

## Project Structure

- `src/app.py`: Flask app factory and route wiring
- `src/api/`: API resources and input/output schemas
- `src/domain/models/`: SQLAlchemy models
- `src/domain/services/`: Task state machine rules
- `src/repositories/`: Data access helpers
- `migrations/`: Alembic migration config and revisions
- `tests/`: unit/integration-style API tests

## Setup (Local)

1. Install `uv`:
   - `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Sync dependencies:
   - `uv sync`
3. Copy environment file:
   - `cp .env.example .env`
4. Run migrations:
   - `uv run alembic upgrade head`
5. Start API:
   - `uv run python main.py`

API will be available at `http://localhost:8000`, docs at `http://localhost:8000/docs`.

## Docker Compose

1. Copy environment file:
   - `cp .env.example .env`
2. Build and run:
   - `docker compose up --build`

The web container runs migrations before launching the app.

## Authentication

### Register

- `POST /auth/register`
- Body:
  - `email` (string)
  - `password` (string, min length 8)

### Login

- `POST /auth/login`
- Body:
  - `email`
  - `password`
- Returns:
  - `access_token`

Use token in header:
- `Authorization: Bearer <access_token>`

## Task Endpoints

- `POST /tasks` (auth required)
- `GET /tasks` (auth required)
- `GET /tasks/{id}` (auth required)
- `PUT /tasks/{id}` (auth required)
- `DELETE /tasks/{id}` (auth required)

### Task Status State Machine

Allowed transitions:
- `new -> running`
- `running -> complete`
- `running -> error`
- `running -> pause`
- `pause -> running`

Invalid transitions return `409 Conflict`.

## Tests

Run tests with:

- `uv run pytest`