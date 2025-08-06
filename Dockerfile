FROM python:3.12-slim

# Install system dependencies in a single layer
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

WORKDIR /app

# Create virtual environment
RUN uv venv .venv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock* ./

# Create the app directory structure that your pyproject.toml expects
RUN mkdir -p app

# Install dependencies (this layer will be cached unless dependencies change)
RUN . .venv/bin/activate && uv sync --frozen

# Copy application code (this layer changes frequently)
COPY . .

EXPOSE 8000

# Use the virtual environment directly
CMD [".venv/bin/python", "run.py"]