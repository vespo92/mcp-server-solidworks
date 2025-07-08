# Multi-stage build for SolidWorks MCP Server
ARG PYTHON_VERSION=3.11

# Stage 1: Build stage with all dependencies
FROM python:${PYTHON_VERSION}-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    # .NET dependencies for PythonNET
    apt-transport-https \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install .NET Runtime for PythonNET
RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y dotnet-runtime-6.0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -e .

# Stage 2: Runtime stage
FROM python:${PYTHON_VERSION}-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    # .NET runtime for PythonNET
    wget \
    apt-transport-https \
    software-properties-common \
    && wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y dotnet-runtime-6.0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 mcp && \
    mkdir -p /app /app/data /app/logs /app/chroma_db && \
    chown -R mcp:mcp /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=mcp:mcp . /app

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # .NET configuration
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 \
    DOTNET_RUNNING_IN_CONTAINER=true \
    # MCP defaults
    MCP_LOG_LEVEL=INFO \
    CHROMA_HOST=chromadb \
    CHROMA_PORT=8000

# Switch to non-root user
USER mcp
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/chroma_db /app/temp /app/exports

# Expose MCP server port (for future HTTP gateway)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; from mcp_server_solidworks.mcp_host.server import SolidWorksMCPServer; sys.exit(0)" || exit 1

# Default command
CMD ["python", "-m", "mcp_server_solidworks.mcp_host.server"]