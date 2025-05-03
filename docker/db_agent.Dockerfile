# syntax=docker/dockerfile:1

### 1) Builder stage
FROM python:3.10-slim AS builder
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY app/agents/database_agent/agent/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps -w /wheels -r requirements.txt

### 2) Runtime stage
FROM python:3.10-slim AS runtime
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy whole repo
COPY . .

EXPOSE 10001

# Uvicorn entrypoint: full module path to your __main__.py
CMD ["uvicorn", "app.agents.database_agent.agent.__main__:app", "--host", "0.0.0.0", "--port", "10001"]
