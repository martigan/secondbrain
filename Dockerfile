FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:${PATH}"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

COPY pyproject.toml README.md ./
RUN uv sync --frozen || uv sync

COPY . .

EXPOSE 8000

CMD ["uv", "run", "python", "main.py"]
