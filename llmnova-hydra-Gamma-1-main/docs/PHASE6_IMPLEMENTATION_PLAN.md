# Phase 6: Observability Implementation Plan

## Overview

This phase implements comprehensive observability capabilities for the Gamma Engine, including **Metrics**, **Tracing**, and **Alerting**. The implementation follows the established patterns from Phases 1-4 and integrates seamlessly with the existing event-driven architecture.

## Background

The Gamma Engine already has:
- Event-driven architecture (`Agent._emit_event` hooks)
- Structured JSON logging (`gamma_engine/core/logger.py`)
- Frontend metrics dashboard (hydra-frontend for static metrics)

We will enhance this with:
- **Runtime metrics collection** (counters, histograms, gauges)
- **Distributed tracing** (span-based request tracking)
- **Intelligent alerting** (threshold-based and anomaly detection)

## User Review Required

> [!IMPORTANT]
> **Technology Stack Decision**
> 
> This plan uses lightweight, self-contained Python libraries to avoid external dependencies:
> - **Metrics**: Custom implementation with Prometheus-compatible export
> - **Tracing**: OpenTelemetry SDK (industry standard, no backend required)
> - **Alerting**: Custom rule engine with pluggable notification handlers
>
> If you prefer using external backends (Prometheus server, Jaeger, etc.), please let me know!

> [!WARNING]
> **Integration Points**
>
> The observability system will be integrated into:
> - Agent execution loop (tracing spans)
> - Tool execution (metrics + tracing)
> - LLM calls (latency tracking)
> - Event emission (custom metrics)
>
> This requires minor modifications to existing core modules.

## Proposed Changes

### Observability Core

#### [NEW] [metrics.py](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/gamma_engine/core/metrics.py)

Implements metrics collection system:
- `MetricsCollector`: Thread-safe singleton for metrics aggregation
- `Counter`: Monotonically increasing values (e.g., total requests)
- `Histogram`: Distribution tracking (e.g., latency percentiles)
- `Gauge`: Point-in-time values (e.g., active tasks)
- Prometheus-compatible export endpoint

**Key metrics to track:**
- Agent execution metrics (iterations, success rate)
- Tool execution metrics (calls per tool, errors, latency)
- LLM metrics (tokens used, API latency, errors)
- System metrics (memory usage, CPU)

#### [NEW] [tracing.py](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/gamma_engine/core/tracing.py)

Implements distributed tracing using OpenTelemetry:
- `TracingService`: Manages trace lifecycle and span creation
- `Span`: Represents a unit of work with timing and metadata
- Context propagation for nested operations
- JSON export for trace visualization

**Instrumented operations:**
- Agent full execution (root span)
- Each LLM call (child span)
- Each tool execution (child span)
- Sub-task decomposition (nested spans)

#### [NEW] [alerting.py](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/gamma_engine/core/alerting.py)

Implements intelligent alerting system:
- `AlertManager`: Centralized alert management
- `AlertRule`: Configurable threshold-based rules
- `AnomalyDetector`: Statistical anomaly detection
- `NotificationHandler`: Abstract interface for notifications
- `EmailHandler`, `WebhookHandler`: Concrete notification implementations
- Alert deduplication and rate limiting

**Alert types:**
- Error rate threshold exceeded
- Latency SLA violations
- Resource exhaustion warnings
- Anomalous behavior detection

---

### Core Module Updates

#### [MODIFY] [agent.py](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/gamma_engine/core/agent.py)

Integrate observability into agent execution:
- Wrap `run()` method with tracing span
- Emit metrics for iterations, tool calls, errors
- Add latency tracking for LLM calls
- Integrate with alert system for failures

**Changes:**
```python
# Add trace span around full execution
# Increment counters for iterations, tool calls
# Record histograms for execution time
# Trigger alerts on max iterations or errors
```

#### [MODIFY] [llm.py](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/gamma_engine/core/llm.py)

Add metrics and tracing to LLM calls:
- Track API latency
- Count tokens used
- Record error rates
- Create spans for each LLM call

#### [MODIFY] [__init__.py](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/gamma_engine/core/__init__.py)

Export new observability components:
```python
from .metrics import MetricsCollector, Counter, Histogram, Gauge
from .tracing import TracingService, Span
from .alerting import AlertManager, AlertRule
```

---

### Configuration

#### [MODIFY] [pyproject.toml](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/pyproject.toml)

Add observability dependencies:
```toml
"opentelemetry-api>=1.20.0",
"opentelemetry-sdk>=1.20.0",
"prometheus-client>=0.19.0",  # For Prometheus export format
"psutil>=5.9.0",  # For system metrics
```

#### [MODIFY] [requirements.txt](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/requirements.txt)

Mirror dependency changes from pyproject.toml.

---

### FastAPI Integration (Optional)

#### [NEW] [observability_endpoints.py](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/backend/observability_endpoints.py)

REST endpoints for observability data:
- `GET /metrics` - Prometheus-formatted metrics
- `GET /traces` - Recent traces in JSON
- `GET /alerts` - Active alerts
- `POST /alerts/rules` - Configure alert rules

---

### Testing

#### [NEW] [test_observability.py](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/tests/test_observability.py)

Comprehensive test suite:
- Test metrics collection and export
- Test trace span creation and nesting
- Test alert rule evaluation
- Test notification handlers
- Integration tests with agent execution

---

### Documentation

#### [NEW] [OBSERVABILITY.md](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/docs/OBSERVABILITY.md)

Complete observability guide:
- Architecture overview
- Metrics reference
- Tracing guide
- Alert configuration
- Integration examples
- Best practices

#### [MODIFY] [ARCHITECTURE.md](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/docs/ARCHITECTURE.md)

Add observability section describing the new components.

#### [MODIFY] [PROGRESSO.md](file:///c:/Users/henri_6m1hz7q/Downloads/llmnova-hydra-Gamma-1/docs/PROGRESSO.md)

Update Phase 6 status to completed.

## Verification Plan

### Automated Tests

1. **Unit Tests**
   ```bash
   cd c:\Users\henri_6m1hz7q\Downloads\llmnova-hydra-Gamma-1
   python -m pytest tests/test_observability.py -v
   ```
   Tests cover:
   - Metrics collection accuracy
   - Trace span hierarchy
   - Alert rule evaluation
   - Notification delivery

2. **Integration Tests**
   ```bash
   python -m pytest tests/test_observability.py::test_agent_observability_integration -v
   ```
   Verifies:
   - Metrics collected during agent execution
   - Traces created for full agent run
   - Alerts triggered on error conditions

### Manual Verification

1. **Create verification script** `verify_phase6.py`:
   - Perform sample agent execution
   - Display collected metrics
   - Show trace hierarchy
   - Trigger test alerts
   - Output: Summary of observability data collected

2. **Run verification**:
   ```bash
   python verify_phase6.py
   ```
   Expected output:
   - Metrics summary (counters, histograms, gauges)
   - Trace visualization (ASCII tree or JSON)
   - Alert history
   - All checks pass ✓

### Metrics Dashboard (Optional)

If time permits, enhance the existing frontend metrics dashboard to display real-time metrics from the backend.

## Dependencies

- ✅ Phase 1: Security system (for secure alert webhooks)
- ✅ Phase 2: Tools (metrics on tool execution)
- ✅ Phase 3: Planning & Messaging (tracing task decomposition)
- ✅ Phase 4: Multimodal (no direct dependency)

## Estimated Complexity

- **Metrics System**: Moderate (4-5 hours)
- **Tracing System**: Moderate (4-5 hours)
- **Alerting System**: High (6-8 hours)
- **Integration**: Moderate (3-4 hours)
- **Testing**: Moderate (3-4 hours)
- **Documentation**: Low (2-3 hours)

**Total**: ~22-29 hours of implementation time.
