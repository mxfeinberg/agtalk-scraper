# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Install uv (modern Python package installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock ./
COPY *.py ./

# Install dependencies using uv
RUN uv sync --frozen

# Set environment variables for the application
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash scraper
USER scraper

# Default command to run the scraper
CMD ["uv", "run", "main.py", "--forum-id", "3", "--max-pages", "100", "--delay", "20.0", "--log-level", "INFO", "--no-file-logging"]