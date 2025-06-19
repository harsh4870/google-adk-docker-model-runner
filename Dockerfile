# Multi-stage build for optimized container size
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Environment variables with defaults
ENV MODEL_NAME=ai/llama3.2:1B-Q8_0
ENV OPENAI_API_KEY=anything
ENV TEST_QUERY="Create a responsive HTML landing page with navigation"
ENV AGENT_TYPE=sequential

# Health check script
COPY --chown=appuser:appuser <<EOF /app/healthcheck.py
#!/usr/bin/env python3
import sys
import os
sys.path.append('/app/agents/shared')

try:
    from config import ModelRunnerConfig
    config = ModelRunnerConfig()
    print(f"✅ Configuration loaded: {config.api_base}")
    sys.exit(0)
except Exception as e:
    print(f"❌ Health check failed: {e}")
    sys.exit(1)
EOF

RUN chmod +x /app/healthcheck.py

# Health check to verify the application can start
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python /app/healthcheck.py || exit 1

# Expose port for web interface
EXPOSE 8000

# Default command - can be overridden
CMD ["python", "-c", "import os; agent=os.getenv('AGENT_TYPE','sequential'); exec(f'import agents.{agent}_agent.agent as agent_module; import asyncio; asyncio.run(agent_module.main())')"]