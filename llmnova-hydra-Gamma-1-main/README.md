
# Gamma Engine

Gamma is a "Google-Grade" Autonomous AI Architecture, evolving from the legacy Hydra/NovaLLM system. It provides a robust backend for AI agents, featuring real-time communication, modular RAG, and extensive tooling.

## Key Features

*   **Agent Core:** Autonomous agent capable of planning and executing tasks using tools.
*   **Real-time Interface:** WebSocket-based communication for chat and status updates.
*   **Modular RAG:**
    *   **Vertex AI:** Production-grade cloud retrieval.
    *   **Local RAG:** Offline capabilities using ChromaDB and SentenceTransformers (supports PDF/Docx/Txt).
    *   **Hybrid Search:** Combines vector similarity with keyword boosting and re-ranking.
*   **Observability:**
    *   `/api/system/status`: Real-time system vitals (CPU/RAM/Disk).
    *   `/metrics`: Prometheus endpoint for monitoring.
*   **Tooling:**
    *   File System, Terminal, Web Development, Google Search.
    *   **SystemStatusTool:** Allows agents to check their own health.
    *   **ModelTrainingTool:** Orchestrates model fine-tuning jobs.

## Architecture

See `docs/gamma_architecture.puml` for a detailed diagram.

## Setup

1.  **Environment:**
    ```bash
    cp .env.example .env
    # Edit .env with your keys (OPENAI_API_KEY, GOOGLE_CLOUD_PROJECT, etc.)
    ```

2.  **Docker:**
    ```bash
    docker-compose up --build
    ```

3.  **Local Development:**
    ```bash
    pip install -r backend/requirements.txt
    uvicorn gamma_server:app --reload
    ```

## Legacy Hydra Migration

This project includes features migrated from the "Hydra" legacy codebase:
- **Local RAG:** Restored offline ingestion capabilities.
- **Metrics Dashboard:** Re-implemented system monitoring.
- **Training Orchestrator:** Added foundation for model fine-tuning workflows.

See `docs/architecture_gap_analysis.md` for details.
