"""
Metrics Collection System for Gamma Engine.

This module provides a comprehensive metrics collection system with support for:
- Counters: Monotonically increasing values
- Histograms: Distribution tracking for latency, sizes, etc.
- Gauges: Point-in-time values that can go up or down

Features:
- Thread-safe singleton pattern
- Label/tag support for multi-dimensional metrics
- Prometheus-compatible export format
- JSON export capability
- System metrics collection (CPU, memory, disk)
"""

import threading
import time
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class MetricType(Enum):
    """Type of metric."""
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"


class Metric:
    """Represents a single metric with its metadata."""
    
    def __init__(
        self,
        name: str,
        metric_type: MetricType,
        value: Any,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[float] = None
    ):
        self.name = name
        self.metric_type = metric_type
        self.value = value
        self.labels = labels or {}
        self.timestamp = timestamp or time.time()
    
    def __repr__(self):
        return f"Metric(name={self.name}, type={self.metric_type.value}, value={self.value})"


class MetricsCollector:
    """
    Thread-safe singleton metrics collector.
    
    Collects and manages metrics for monitoring agent performance.
    Supports counters, histograms, and gauges with optional labels.
    
    Example:
        >>> metrics = MetricsCollector.get_instance()
        >>> metrics.increment("requests.total")
        >>> metrics.record("latency.ms", 125.5)
        >>> metrics.set_gauge("active.connections", 42)
    """
    
    _instance: Optional['MetricsCollector'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __init__(self):
        """Initialize the metrics collector."""
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._metric_lock = threading.Lock()
        self._enabled = True
    
    @classmethod
    def get_instance(cls) -> 'MetricsCollector':
        """
        Get the singleton instance of MetricsCollector.
        
        Returns:
            The singleton MetricsCollector instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def enable(self) -> None:
        """Enable metrics collection."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable metrics collection."""
        self._enabled = False
    
    def reset(self) -> None:
        """Clear all collected metrics."""
        with self._metric_lock:
            self._metrics.clear()
    
    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name (e.g., "requests.total")
            value: Amount to increment by (default: 1.0)
            labels: Optional labels for metric dimensions
        
        Example:
            >>> metrics.increment("http.requests", labels={"method": "GET", "status": "200"})
        """
        if not self._enabled:
            return
        
        key = self._get_metric_key(name, labels)
        
        with self._metric_lock:
            if key not in self._metrics:
                self._metrics[key] = {
                    "type": MetricType.COUNTER,
                    "value": 0.0,
                    "labels": labels or {},
                }
            
            self._metrics[key]["value"] += value
            self._metrics[key]["timestamp"] = time.time()
    
    def record(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a value in a histogram metric.
        
        Args:
            name: Metric name (e.g., "latency.ms")
            value: Value to record
            labels: Optional labels for metric dimensions
        
        Example:
            >>> metrics.record("api.latency_ms", 125.5, labels={"endpoint": "/users"})
        """
        if not self._enabled:
            return
        
        key = self._get_metric_key(name, labels)
        
        with self._metric_lock:
            if key not in self._metrics:
                self._metrics[key] = {
                    "type": MetricType.HISTOGRAM,
                    "value": [],
                    "labels": labels or {},
                }
            
            self._metrics[key]["value"].append(value)
            self._metrics[key]["timestamp"] = time.time()
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric to a specific value.
        
        Args:
            name: Metric name (e.g., "active.connections")
            value: Current value
            labels: Optional labels for metric dimensions
        
        Example:
            >>> metrics.set_gauge("memory.usage_mb", 512.5)
        """
        if not self._enabled:
            return
        
        key = self._get_metric_key(name, labels)
        
        with self._metric_lock:
            self._metrics[key] = {
                "type": MetricType.GAUGE,
                "value": value,
                "labels": labels or {},
                "timestamp": time.time()
            }
    
    def get_metric(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[Metric]:
        """
        Get a specific metric.
        
        Args:
            name: Metric name
            labels: Optional labels to match
        
        Returns:
            Metric object or None if not found
        """
        key = self._get_metric_key(name, labels)
        
        with self._metric_lock:
            metric_data = self._metrics.get(key)
            if metric_data:
                return Metric(
                    name=name,
                    metric_type=metric_data["type"],
                    value=metric_data["value"],
                    labels=metric_data.get("labels", {}),
                    timestamp=metric_data.get("timestamp", time.time())
                )
        
        return None
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all collected metrics.
        
        Returns:
            Dictionary of all metrics
        """
        with self._metric_lock:
            return self._metrics.copy()
    
    def collect_system_metrics(self) -> None:
        """
        Collect system-level metrics (CPU, memory, disk usage).
        
        Requires psutil library to be installed.
        """
        if not self._enabled or not PSUTIL_AVAILABLE:
            return
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.set_gauge("system.cpu_percent", cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.set_gauge("system.memory_percent", memory.percent)
            self.set_gauge("system.memory_mb", memory.used / (1024 * 1024))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.set_gauge("system.disk_percent", disk.percent)
            self.set_gauge("system.disk_free_gb", disk.free / (1024 ** 3))
            
        except Exception as e:
            # Silently fail if system metrics can't be collected
            pass
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            Prometheus-formatted metrics string
        
        Example output:
            # HELP requests_total requests.total
            # TYPE requests_total counter
            requests_total{method="GET"} 42.0
        """
        lines = []
        
        with self._metric_lock:
            # Group metrics by name
            grouped = defaultdict(list)
            for key, metric in self._metrics.items():
                # Extract base metric name (without labels)
                name = key.split("{")[0] if "{" in key else key
                grouped[name].append((key, metric))
            
            # Export each metric group
            for name, metrics in sorted(grouped.items()):
                # Convert dots to underscores for Prometheus
                prom_name = name.replace(".", "_")
                metric_type = metrics[0][1]["type"].value
                
                # Add HELP and TYPE
                lines.append(f"# HELP {prom_name} {name}")
                lines.append(f"# TYPE {prom_name} {metric_type}")
                
                # Add metric values
                for key, metric_data in metrics:
                    labels_str = self._format_prometheus_labels(metric_data["labels"])
                    
                    if metric_data["type"] == MetricType.HISTOGRAM:
                        # For histograms, export count and sum
                        if metric_data["value"]:
                            values = metric_data["value"]
                            lines.append(f"{prom_name}_count{labels_str} {len(values)}")
                            lines.append(f"{prom_name}_sum{labels_str} {sum(values)}")
                            
                            # Calculate percentiles
                            sorted_values = sorted(values)
                            p50_idx = int(len(sorted_values) * 0.50)
                            p95_idx = int(len(sorted_values) * 0.95)
                            p99_idx = int(len(sorted_values) * 0.99)
                            
                            if sorted_values:
                                lines.append(f"{prom_name}_p50{labels_str} {sorted_values[p50_idx]}")
                                lines.append(f"{prom_name}_p95{labels_str} {sorted_values[p95_idx]}")
                                lines.append(f"{prom_name}_p99{labels_str} {sorted_values[p99_idx]}")
                    else:
                        # For counters and gauges, just export the value
                        lines.append(f"{prom_name}{labels_str} {metric_data['value']}")
                
                lines.append("")  # Empty line between metrics
        
        return "\n".join(lines)
    
    def export_json(self) -> Dict[str, Dict[str, Any]]:
        """
        Export metrics as JSON.
        
        Returns:
            Dictionary with all metrics data
        """
        with self._metric_lock:
            return {
                key: {
                    "type": value["type"].value,
                    "value": value["value"],
                    "labels": value["labels"],
                    "timestamp": value.get("timestamp", 0)
                }
                for key, value in self._metrics.items()
            }
    
    @staticmethod
    def _get_metric_key(name: str, labels: Optional[Dict[str, str]]) -> str:
        """
        Generate a unique key for a metric with labels.
        
        Args:
            name: Metric name
            labels: Optional labels
        
        Returns:
            Unique metric key in format: name{label1="value1",label2="value2"}
        """
        if not labels:
            return name
        
        # Sort labels for consistent keys
        sorted_labels = sorted(labels.items())
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted_labels)
        return f"{name}{{{label_str}}}"
    
    @staticmethod
    def _format_prometheus_labels(labels: Dict[str, str]) -> str:
        """
        Format labels for Prometheus export.
        
        Args:
            labels: Label dictionary
        
        Returns:
            Formatted label string in Prometheus format
        """
        if not labels:
            return ""
        
        sorted_labels = sorted(labels.items())
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted_labels)
        return "{" + label_str + "}"


def get_metrics_collector() -> MetricsCollector:
    """
    Convenience function to get the MetricsCollector singleton.
    
    Returns:
        The singleton MetricsCollector instance
    
    Example:
        >>> from gamma_engine.core.metrics import get_metrics_collector
        >>> metrics = get_metrics_collector()
        >>> metrics.increment("requests.total")
    """
    return MetricsCollector.get_instance()
