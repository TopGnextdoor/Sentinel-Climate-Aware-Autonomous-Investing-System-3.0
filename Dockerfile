FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install uv

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv into the system python environment
RUN uv pip install --system -r pyproject.toml

# Copy the rest of the application
COPY . .

# Expose the requested port
EXPOSE 8080

# Environment variables for API keys
# These can be overridden at runtime
ENV GEMINI_API_KEY=""
ENV GEMINI_API_KEY_DEV=""
ENV GEMINI_API_KEY_PROD=""
ENV ALPACA_KEY=""
ENV ALPACA_SECRET=""

# Start the FastAPI server on dynamic port (Render support)
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
