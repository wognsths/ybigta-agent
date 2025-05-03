# syntax=docker/dockerfile:1

### 1) Builder stage
FROM python:3.10-slim AS builder
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY app/agents/database_agent/database/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps -w /wheels -r requirements.txt

### 2) Runtime stage
FROM python:3.10-slim AS runtime
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy everything from repo root
COPY . .

EXPOSE 8080

# Point Uvicorn at the full module path, from /app
CMD ["uvicorn", "app.agents.database_agent.database.main:app", "--host", "0.0.0.0", "--port", "8080"]
