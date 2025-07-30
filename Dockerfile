FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
RUN pip install uv

WORKDIR /app

# Copy pyproject.toml first for better layer caching
COPY pyproject.toml ./

RUN uv venv .venv
RUN . .venv/bin/activate

# Copy application code first, because "app" config inside the pyproject.toml file
COPY . .

RUN uv pip install .

EXPOSE 8000

CMD ["uv", "run", "run.py"]