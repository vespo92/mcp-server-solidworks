# Makefile for SolidWorks MCP Server Docker Operations

.PHONY: help build up down restart logs shell test clean dev jupyter

# Default target
help:
	@echo "SolidWorks MCP Server - Docker Commands"
	@echo "======================================"
	@echo "make build       - Build all Docker images"
	@echo "make up          - Start MCP server and ChromaDB"
	@echo "make down        - Stop all containers"
	@echo "make restart     - Restart all containers"
	@echo "make logs        - View container logs"
	@echo "make shell       - Open shell in MCP server container"
	@echo "make test        - Run tests in container"
	@echo "make clean       - Clean up containers and volumes"
	@echo "make dev         - Start development environment"
	@echo "make jupyter     - Start Jupyter notebook server"
	@echo ""
	@echo "Advanced Commands:"
	@echo "make build-nocache - Build without cache"
	@echo "make logs-f        - Follow logs"
	@echo "make chromadb-only - Start only ChromaDB"
	@echo "make status        - Show container status"

# Build all images
build:
	docker-compose build

# Build without cache
build-nocache:
	docker-compose build --no-cache

# Start services
up:
	docker-compose up -d
	@echo "✅ SolidWorks MCP Server started!"
	@echo "📊 ChromaDB available at: http://localhost:8057"
	@echo "🔍 View logs with: make logs"

# Start only ChromaDB
chromadb-only:
	docker-compose up -d chromadb
	@echo "✅ ChromaDB started on port 8057"

# Stop services
down:
	docker-compose down
	@echo "🛑 All services stopped"

# Restart services
restart:
	docker-compose restart
	@echo "🔄 Services restarted"

# View logs
logs:
	docker-compose logs

# Follow logs
logs-f:
	docker-compose logs -f

# Open shell in MCP server
shell:
	docker-compose exec mcp-server /bin/bash

# Run tests
test:
	docker-compose exec mcp-server python -m pytest tests/ -v

# Clean up everything
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "🧹 Cleanup complete"

# Start development environment
dev:
	docker-compose --profile dev up -d
	docker-compose exec dev-tools /bin/bash

# Start Jupyter notebook
jupyter:
	docker-compose --profile jupyter up -d jupyter
	@echo "📓 Jupyter Lab available at: http://localhost:8888"
	@echo "   No password required"

# Show container status
status:
	@echo "Container Status:"
	@echo "================="
	@docker-compose ps

# Build C# adapters in container
build-adapters:
	docker-compose run --rm dev-tools python scripts/build_adapters.py

# Run installation test
test-install:
	docker-compose run --rm mcp-server python scripts/test_installation.py

# Initialize ChromaDB with sample data
init-knowledge:
	docker-compose exec mcp-server python -c "from src.context_builder.knowledge_base import SolidWorksKnowledgeBase; kb = SolidWorksKnowledgeBase(); print('Knowledge base initialized')"

# Export ChromaDB data
export-knowledge:
	docker-compose exec mcp-server python -c "from src.context_builder.knowledge_base import SolidWorksKnowledgeBase; kb = SolidWorksKnowledgeBase(); kb.export_knowledge('/app/data/knowledge_export.json')"
	@echo "📦 Knowledge exported to ./data/knowledge_export.json"

# Watch logs for specific service
logs-%:
	docker-compose logs -f $*

# Execute command in container
exec:
	docker-compose exec mcp-server $(CMD)

# Quick development cycle
quick: down build up logs-f