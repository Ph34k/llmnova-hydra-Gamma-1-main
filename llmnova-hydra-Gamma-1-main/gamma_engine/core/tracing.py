"""
Distributed Tracing System for Gamma Engine.

This module provides OpenTelemetry-style distributed tracing capabilities:
- Span creation and management
- Hierarchical trace tracking
- Automatic context propagation
- Event recording within spans
- Error tracking and status management

Features:
- Thread-safe singleton pattern
- Context manager API for easy span management
- Automatic timing capture
- Multiple export formats (JSON, ASCII tree)
- Trace filtering and querying
"""

import threading
import time
import traceback
import uuid
from contextlib import contextmanager
from enum import Enum
from typing import Any, Dict, Generator, List, Optional


class SpanStatus(Enum):
    """Status of a span."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


class SpanEvent:
    """Represents an event within a span."""
    
    def __init__(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None
    ):
        self.name = name
        self.attributes = attributes or {}
        self.timestamp = timestamp or time.time()
    
    def __repr__(self):
        return f"SpanEvent(name={self.name}, timestamp={self.timestamp})"


class SpanData:
    """Complete data for a finished span."""
    
    def __init__(
        self,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str],
        name: str,
        start_time: float,
        end_time: float,
        duration_ms: float,
        attributes: Dict[str, Any],
        events: List[SpanEvent],
        status: SpanStatus,
        error: Optional[str]
    ):
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.duration_ms = duration_ms
        self.attributes = attributes
        self.events = events
        self.status = status
        self.error = error
    
    def __repr__(self):
        return f"SpanData(name={self.name}, duration={self.duration_ms:.2f}ms, status={self.status.value})"


class SpanContext:
    """
    Context for an active span.
    
    Provides methods to add attributes, events, and set status
    during span execution.
    """
    
    def __init__(
        self,
        span_id: Optional[str],
        tracer: 'TracingService',
        name: str = "",
        attributes: Optional[Dict[str, Any]] = None
    ):
        self._span_id = span_id
        self._tracer = tracer
        self._name = name
        self._attributes = attributes or {}
        self._events: List[SpanEvent] = []
        self._status = SpanStatus.UNSET
        self._error: Optional[str] = None
    
    def set_attribute(self, key: str, value: Any) -> 'SpanContext':
        """
        Set an attribute on the span.
        
        Args:
            key: Attribute key
            value: Attribute value
        
        Returns:
            Self for method chaining
        
        Example:
            >>> span.set_attribute("user_id", "123")
            >>> span.set_attribute("request_id", "abc-def")
        """
        self._attributes[key] = value
        return self
    
    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> 'SpanContext':
        """
        Add a timestamped event to the span.
        
        Args:
            name: Event name
            attributes: Optional event attributes
        
        Returns:
            Self for method chaining
        
        Example:
            >>> span.add_event("validation_started")
            >>> span.add_event("data_processed", {"rows": 100})
        """
        event = SpanEvent(name, attributes)
        self._events.append(event)
        return self
    
    def set_status(
        self,
        status: SpanStatus,
        error: Optional[str] = None
    ) -> 'SpanContext':
        """
        Set the span status.
        
        Args:
            status: Span status (OK, ERROR, UNSET)
            error: Optional error message (for ERROR status)
        
        Returns:
            Self for method chaining
        
        Example:
            >>> span.set_status(SpanStatus.OK)
            >>> span.set_status(SpanStatus.ERROR, "Connection failed")
        """
        self._status = status
        self._error = error
        return self


class TracingService:
    """
    Thread-safe singleton tracing service.
    
    Provides OpenTelemetry-style distributed tracing with span
    creation, hierarchical tracking, and multiple export formats.
    
    Example:
        >>> tracer = TracingService.get_instance()
        >>> with tracer.start_span("operation") as span:
        ...     span.set_attribute("key", "value")
        ...     # Do work
        ...     span.set_status(SpanStatus.OK)
    """
    
    _instance: Optional['TracingService'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __init__(self):
        """Initialize the tracing service."""
        self._enabled = True
        self._spans: List[SpanData] = []
        self._span_lock = threading.Lock()
        self._active_spans: Dict[str, SpanContext] = {}
        self._span_stack = threading.local()
    
    @classmethod
    def get_instance(cls) -> 'TracingService':
        """
        Get the singleton instance of TracingService.
        
        Returns:
            The singleton TracingService instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def enable(self) -> None:
        """Enable tracing."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable tracing."""
        self._enabled = False
    
    def reset(self) -> None:
        """Clear all collected traces."""
        with self._span_lock:
            self._spans.clear()
            self._active_spans.clear()
    
    @contextmanager
    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None
    ) -> Generator[SpanContext, None, None]:
        """
        Start a new span with context manager support.
        
        Args:
            name: Span name (e.g., "database.query", "api.request")
            attributes: Optional initial attributes
            parent_span_id: Optional parent span ID for hierarchies
        
        Yields:
            SpanContext for adding attributes, events, and status
        
        Example:
            >>> with tracer.start_span("process_request") as span:
            ...     span.set_attribute("user_id", "123")
            ...     # Do processing
            ...     span.set_status(SpanStatus.OK)
        """
        # If tracing is disabled, yield a dummy context
        if not self._enabled:
            yield SpanContext(None, self)
            return
        
        # Generate IDs
        span_id = str(uuid.uuid4())[:8]
        trace_id = str(uuid.uuid4())[:16]
        
        # Record start time
        start_time = time.time()
        
        # Create span context
        span_ctx = SpanContext(span_id, self, name, attributes or {})
        
        # Store active span
        with self._span_lock:
            self._active_spans[span_id] = span_ctx
        
        try:
            yield span_ctx
        except Exception as e:
            # Automatically mark span as error on exception
            span_ctx.set_status(
                SpanStatus.ERROR,
                f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            )
            raise
        finally:
            # Record end time and duration
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Create span data
            span_data = SpanData(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                name=name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                attributes=span_ctx._attributes.copy(),
                events=span_ctx._events.copy(),
                status=span_ctx._status,
                error=span_ctx._error
            )
            
            # Store completed span
            with self._span_lock:
                self._spans.append(span_data)
                if span_id in self._active_spans:
                    del self._active_spans[span_id]
    
    def get_traces(
        self,
        limit: Optional[int] = None,
        trace_id: Optional[str] = None
    ) -> List[SpanData]:
        """
        Get collected trace spans.
        
        Args:
            limit: Optional limit on number of spans returned
            trace_id: Optional filter by trace ID
        
        Returns:
            List of SpanData objects
        """
        with self._span_lock:
            spans = self._spans.copy()
        
        # Filter by trace_id if specified
        if trace_id:
            spans = [s for s in spans if s.trace_id == trace_id]
        
        # Sort by start time (most recent first)
        spans.sort(key=lambda s: s.start_time, reverse=True)
        
        # Apply limit
        if limit:
            spans = spans[:limit]
        
        return spans
    
    def export_traces(self) -> List[Dict[str, Any]]:
        """
        Export all traces as JSON-serializable dictionaries.
        
        Returns:
            List of trace dictionaries
        """
        spans = self.get_traces()
        return [
            {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "parent_span_id": span.parent_span_id,
                "name": span.name,
                "start_time": span.start_time,
                "end_time": span.end_time,
                "duration_ms": span.duration_ms,
                "attributes": span.attributes,
                "events": [
                    {
                        "name": event.name,
                        "attributes": event.attributes,
                        "timestamp": event.timestamp
                    }
                    for event in span.events
                ],
                "status": span.status.value,
                "error": span.error
            }
            for span in spans
        ]
    
    def export_trace_tree(self, trace_id: Optional[str] = None) -> str:
        """
        Export traces as an ASCII tree visualization.
        
        Args:
            trace_id: Optional trace ID to filter by
        
        Returns:
            ASCII tree string representation
        
        Example output:
            └── agent.run (1250.5ms) ✓
                ├── llm.call (450.2ms) ✓
                └── tool.search (300.1ms) ✓
        """
        spans = self.get_traces(trace_id=trace_id)
        
        if not spans:
            return "No traces found"
        
        lines = []
        
        # Build tree structure
        span_by_id = {span.span_id: span for span in spans}
        roots = [span for span in spans if span.parent_span_id is None]
        
        def render_span(span: SpanData, prefix: str = "", is_last: bool = True):
            """Recursively render span and its children."""
            # Status icon
            if span.status == SpanStatus.OK:
                status_icon = "✓"
            elif span.status == SpanStatus.ERROR:
                status_icon = "✗"
            else:
                status_icon = "○"
            
            # Tree connector
            connector = "└── " if is_last else "├── "
            
            # Span info
            line = f"{prefix}{connector}{span.name} ({span.duration_ms:.1f}ms) {status_icon}"
            lines.append(line)
            
            # Add attributes if any
            if span.attributes:
                attr_prefix = prefix + ("    " if is_last else "│   ")
                attr_str = ", ".join(f"{k}={v}" for k, v in list(span.attributes.items())[:3])
                if len(span.attributes) > 3:
                    attr_str += "..."
                lines.append(f"{attr_prefix}[{attr_str}]")
            
            # Find and render children
            children = [s for s in spans if s.parent_span_id == span.span_id]
            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                child_prefix = prefix + ("    " if is_last else "│   ")
                render_span(child, child_prefix, is_last_child)
        
        # Render all root spans
        for i, root in enumerate(roots):
            is_last_root = (i == len(roots) - 1)
            render_span(root, "", is_last_root)
        
        return "\n".join(lines)


def get_tracer() -> TracingService:
    """
    Convenience function to get the TracingService singleton.
    
    Returns:
        The singleton TracingService instance
    
    Example:
        >>> from gamma_engine.core.tracing import get_tracer, SpanStatus
        >>> tracer = get_tracer()
        >>> with tracer.start_span("operation") as span:
        ...     span.set_status(SpanStatus.OK)
    """
    return TracingService.get_instance()
