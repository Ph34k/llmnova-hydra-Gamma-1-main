# Gamma Architecture

## Overview
Gamma is an autonomous AI software engineer designed to rival top-tier agents. It employs a **Cognitive Architecture** inspired by human reasoning:

1.  **Perception**: Tools like `ListFiles`, `ReadFile`, and `BrowserTool` gather context.
2.  **Memory**: `gamma_engine.core.memory` manages context windows and history.
3.  **Reasoning (Brain)**: `gamma_engine.core.brain` decomposes high-level goals into a dependency graph of tasks.
4.  **Critique**: Before execution, a "Critic" agent reviews generated code/plans (`LLMProvider.critique`).
5.  **Execution**: Safe execution of tools via the `Agent` loop.
6.  **Reflection**: The agent analyzes tool outputs to adjust its plan.

## Core Modules

### `gamma_engine.core`
-   **Agent**: The main orchestrator loop.
-   **Brain**: Handles high-level planning and decomposition.
-   **LLMProvider**: Abstraction over OpenAI/Anthropic APIs with retry logic and error handling.
-   **Memory**: Manages conversation history.

### `gamma_engine.tools`
-   **Filesystem**: Safe file operations.
-   **Terminal**: Sandboxed shell execution.
-   **Browser**: Web research capabilities.
-   **Vision**: Screenshot analysis.

### `gamma_engine.core.observability`
-   **MetricsCollector**: Real-time performance metrics (counters, histograms, gauges).
-   **TracingService**: OpenTelemetry-based distributed tracing for request flows.
-   **AlertManager**: Intelligent alerting with threshold rules and anomaly detection.
-   **Integration**: Automatic instrumentation of Agent, LLM, and Tool execution.

## Frontend
-   **Next.js 14**: App Router based modern UI.
-   **Neural Interface**: Visualizes the "Thinking" process via WebSockets.
-   **Workspace**: Integrates Monaco Editor for real-time code viewing.
-   **Live Preview**: Iframe integration to see the generated app running.

## Deployment
-   **Docker**: Multi-stage builds for optimization.
-   **Nginx**: Reverse proxy for production traffic handling.
-   **FastAPI**: High-performance async backend.
