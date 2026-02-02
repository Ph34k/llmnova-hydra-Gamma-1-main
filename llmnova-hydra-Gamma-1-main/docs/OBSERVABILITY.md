# Observability System

## Overview

The Gamma Engine observability system provides comprehensive monitoring of agent execution through **metrics collection**, **distributed tracing**, and **intelligent alerting**. This enables deep insights into performance, behavior, and potential issues.

## Architecture

### Components

1. **MetricsCollector** (`gamma_engine.core.metrics`)
   - Thread-safe singleton for collecting metrics
   - Supports counters, histograms, and gauges
   - Prometheus-compatible export format
   - Automatic system metrics collection

2. **TracingService** (`gamma_engine.core.tracing`)
   - OpenTelemetry-based distributed tracing
   - Hierarchical span tracking
   - Automatic context propagation
   - ASCII tree visualization

3. **AlertManager** (`gamma_engine.core.alerting`)
   - Threshold-based alert rules
   - Statistical anomaly detection
   - Pluggable notification handlers
   - Alert deduplication and cooldown

### Integration Points

The observability system is automatically integrated into:
- **Agent execution**: Full run traced with metrics
- **LLM calls**: Latency and token tracking
- **Tool execution**: Per-tool metrics and traces
- **Error handling**: Automatic error tracking

## Quick Start

### Basic Usage

```python
from gamma_engine.core.metrics import get_metrics_collector
from gamma_engine.core.tracing import get_tracer
from gamma_engine.core.alerting import get_alert_manager, AlertRule, AlertSeverity

# Get singletons
metrics = get_metrics_collector()
tracer = get_tracer()
alerts = get_alert_manager()

# Collect metrics
metrics.increment("my.counter")
metrics.record("my.latency_ms", 125.5)
metrics.set_gauge("my.active_tasks", 3)

# Create traces
with tracer.start_span("my.operation") as span:
    span.set_attribute("user_id", "123")
    # Do work
    span.set_status(SpanStatus.OK)

# Set up alerts
rule = AlertRule(
    name="high_latency",
    metric_name="my.latency_ms",
    threshold=200.0,
    severity=AlertSeverity.WARNING
)
alerts.add_rule(rule)
alerts.check_metrics()
```

## Metrics System

### Metric Types

#### Counters
Monotonically increasing values for tracking cumulative metrics:

```python
metrics.increment("requests.total")
metrics.increment("tokens.consumed", value=150)
metrics.increment("http.requests", labels={"method": "GET", "status": "200"})
```

**Use for:** Request counts, error counts, total operations

#### Histograms
Distribution tracking for latency, sizes, durations:

```python
metrics.record("api.latency_ms", 125.5)
metrics.record("response.size_bytes", 1024)
metrics.record("tool.duration_ms", 50.0, labels={"tool": "search"})
```

**Use for:** Latencies, response times, request sizes

#### Gauges
Point-in-time values that can go up or down:

```python
metrics.set_gauge("active.connections", 42)
metrics.set_gauge("memory.usage_mb", 512.5)
metrics.set_gauge("queue.depth", 10)
```

**Use for:** Current values, active connections, queue depths

### Built-in Metrics

The Agent automatically collects:

| Metric | Type | Description |
|--------|------|-------------|
| `agent.runs.total` | Counter | Total agent executions |
| `agent.iterations.total` | Counter | Total planning iterations |
| `agent.run_duration_ms` | Histogram | Full execution time |
| `agent.max_iterations_reached` | Counter | Executions hitting limit |
| `agent.errors.total` | Counter | Total agent errors |
| `llm.latency_ms` | Histogram | LLM API latency |
| `tools.calls.total` | Counter | Tool executions (labeled by tool) |
| `tools.execution_time_ms` | Histogram | Tool execution time |
| `tools.errors.total` | Counter | Tool errors (labeled) |
| `system.cpu_percent` | Gauge | CPU usage % |
| `system.memory_percent` | Gauge | Memory usage % |

### System Metrics

Collect system-level metrics:

```python
metrics.collect_system_metrics()

cpu = metrics.get_metric("system.cpu_percent")
memory = metrics.get_metric("system.memory_percent")
```

### Exporting Metrics

#### Prometheus Format

```python
prometheus_text = metrics.export_prometheus()
print(prometheus_text)
```

Output:
```
# HELP agent_runs_total agent.runs.total
# TYPE agent_runs_total counter
agent_runs_total 42.0

# HELP llm_latency_ms llm.latency_ms
# TYPE llm_latency_ms histogram
llm_latency_ms_count 10
llm_latency_ms_sum 1250.5
llm_latency_ms_p50 120.0
llm_latency_ms_p95 180.0
```

#### JSON Format

```python
import json
metrics_data = metrics.export_json()
print(json.dumps(metrics_data, indent=2))
```

## Distributed Tracing

### Creating Spans

Spans represent units of work in your system:

```python
with tracer.start_span("database.query") as span:
    span.set_attribute("query", "SELECT * FROM users")
    span.set_attribute("database", "postgres")
    
    result = execute_query()
    
    span.set_attribute("rows", len(result))
    span.set_status(SpanStatus.OK)
```

### Nested Spans

Create hierarchical traces:

```python
with tracer.start_span("handle_request") as request_span:
    request_span.set_attribute("path", "/api/process")
    
    with tracer.start_span("validate_input") as validate_span:
        # Validation logic
        validate_span.set_status(SpanStatus.OK)
    
    with tracer.start_span("process_data") as process_span:
        # Processing logic
        process_span.set_status(SpanStatus.OK)
    
    request_span.set_status(SpanStatus.OK)
```

### Span Events

Add timestamped events within spans:

```python
with tracer.start_span("file_upload") as span:
    span.add_event("validation_started")
    # Validate
    span.add_event("validation_completed", {"valid": True})
    
    span.add_event("upload_started")
    # Upload
    span.add_event("upload_completed", {"bytes": 1024})
```

### Error Tracking

Automatically capture errors:

```python
try:
    with tracer.start_span("risky_operation") as span:
        raise ValueError("Something went wrong")
except ValueError:
    # Span automatically marked as ERROR with exception details
    pass
```

### Viewing Traces

#### Get Recent Traces

```python
recent_traces = tracer.get_traces(limit=10)
for span in recent_traces:
    print(f"{span.name}: {span.duration_ms:.2f}ms")
```

#### ASCII Tree Visualization

```python
print(tracer.export_trace_tree())
```

Output:
```
└── agent.run (1250.5ms) ✓
    ├── llm.call (450.2ms) ✓
    ├── tool.search (300.1ms) ✓ [args={"query": "test"}]
    └── tool.read_file (150.0ms) ✓
```

#### JSON Export

```python
import json
traces = tracer.export_traces()
print(json.dumps(traces, indent=2))
```

## Alerting System

### Creating Alert Rules

Define threshold-based alerts:

```python
from gamma_engine.core.alerting import (
    AlertRule, AlertSeverity, AlertOperator, ConsoleHandler
)

# High error rate alert
error_rule = AlertRule(
    name="high_error_rate",
    metric_name="agent.errors.total",
    threshold=10.0,
    operator=AlertOperator.GREATER_THAN,
    severity=AlertSeverity.ERROR,
    message_template="Error rate exceeded: {value} (threshold: {threshold})"
)

alerts.add_rule(error_rule)
```

### Alert Operators

- `AlertOperator.GREATER_THAN` - Value > threshold
- `AlertOperator.LESS_THAN` - Value < threshold
- `AlertOperator.GREATER_EQUAL` - Value >= threshold
- `AlertOperator.LESS_EQUAL` - Value <= threshold
- `AlertOperator.EQUALS` - Value == threshold
- `AlertOperator.NOT_EQUALS` - Value != threshold

### Severity Levels

- `AlertSeverity.INFO` - Informational
- `AlertSeverity.WARNING` - Warning condition
- `AlertSeverity.ERROR` - Error condition
- `AlertSeverity.CRITICAL` - Critical issue

### Notification Handlers

#### Console Handler

```python
from gamma_engine.core.alerting import ConsoleHandler

handler = ConsoleHandler()
alerts.add_handler(handler)
```

#### Email Handler

```python
from gamma_engine.core.alerting import EmailHandler

email_handler = EmailHandler(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    from_email="alerts@example.com",
    to_emails=["admin@example.com"],
    username="alerts@example.com",
    password="app_password"
)

alerts.add_handler(email_handler)
```

#### Webhook Handler

```python
from gamma_engine.core.alerting import WebhookHandler

webhook_handler = WebhookHandler(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    headers={"Content-Type": "application/json"}
)

alerts.add_handler(webhook_handler)
```

### Checking Alerts

Manually trigger alert evaluation:

```python
triggered = alerts.check_metrics()
for alert in triggered:
    print(f"Alert: {alert.rule_name} - {alert.message}")
```

### Alert Cooldown

Prevent alert spam with cooldown periods:

```python
rule = AlertRule(
    name="cpu_threshold",
    metric_name="system.cpu_percent",
    threshold=90.0,
    cooldown_seconds=300  # 5 minutes between alerts
)
```

### Viewing Alert History

```python
# All alerts
all_alerts = alerts.get_alerts()

# Filter by severity
critical_alerts = alerts.get_alerts(severity=AlertSeverity.CRITICAL)

# Limit results
recent_alerts = alerts.get_alerts(limit=10)
```

## Best Practices

### Metrics

1. **Use descriptive names**: `agent.runs.total` not `runs`
2. **Add labels for dimensions**: `labels={"tool": "search", "status": "success"}`
3. **Choose appropriate types**: Counters for totals, histograms for latencies
4. **Collect system metrics**: Monitor resource usage proactively

### Tracing

1. **Trace complete operations**: Start at entry points
2. **Use meaningful span names**: `tool.search` not `execute`
3. **Add relevant attributes**: User IDs, request IDs, parameters
4. **Record events for milestones**: Major steps within an operation
5. **Set appropriate status**: Always call `set_status()` before span ends

### Alerting

1. **Set realistic thresholds**: Based on actual baseline metrics
2. **Use appropriate severity**: Don't mark everything as CRITICAL
3. **Configure cooldown**: Prevent notification fatigue
4. **Test alerts**: Verify rules trigger correctly
5. **Document alerts**: Explain what each alert means and how to respond

## Configuration

### Disabling Observability

```python
# Disable metrics
metrics.disable()

# Disable tracing
tracer.disable()

# Disable alerting
alerts.disable()
```

### Resetting State

```python
# Clear all metrics
metrics.reset()

# Clear all traces
tracer.reset()

# Clear alert history
alerts.clear_alerts()
```

## Troubleshooting

### High Memory Usage

If metrics/traces consume too much memory:

```python
# Periodically reset old data
import time
last_reset = time.time()

if time.time() - last_reset > 3600:  # Every hour
    tracer.reset()  # Clear old traces
    last_reset = time.time()
```

### Missing Metrics

If expected metrics aren't appearing:

1. Verify observability is enabled: `metrics._enabled`
2. Check metric name spelling
3. Ensure metrics are being incremented/recorded
4. Call `metrics.collect_system_metrics()` for system metrics

### Alerts Not Triggering

If alerts don't fire:

1. Verify rule is enabled: `rule.enabled`
2. Check threshold values are correct
3. Ensure `alerts.check_metrics()` is being called
4. Check cooldown hasn't prevented triggering
5. Verify metric exists: `metrics.get_metric(name)`

## Performance Impact

The observability system is designed for minimal overhead:

- **Metrics**: ~0.1ms per operation
- **Tracing**: ~0.5ms per span
- **Alerting**: ~1ms per check (depends on rule count)

For production deployments with high throughput, consider:
- Sampling traces (trace 10% of requests)
- Limiting histogram retention
- Batching alert checks

## Examples

See `verify_phase6.py` for comprehensive examples of all observability features.
