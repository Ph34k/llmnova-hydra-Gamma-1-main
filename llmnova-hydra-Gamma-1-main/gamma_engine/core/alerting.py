"""
Intelligent Alerting System for Gamma Engine.

This module provides a comprehensive alerting system with:
- Threshold-based alert rules
- Multiple comparison operators
- Severity levels
- Cooldown periods to prevent alert spam
- Pluggable notification handlers (Email, Webhook, Console)
- Alert history tracking

Features:
- Thread-safe singleton pattern
- Automatic metric evaluation
- Multiple notification channels
- Alert deduplication
- Statistical anomaly detection
"""

import threading
import time
from enum import Enum
from statistics import mean, stdev
from typing import Any, Dict, List, Optional

from .metrics import MetricsCollector, MetricType


class AlertSeverity(Enum):
    """Severity level of an alert."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertOperator(Enum):
    """Comparison operator for alert rules."""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="


class AlertRule:
    """
    Defines a threshold-based alert rule.
    
    Attributes:
        name: Unique rule name
        metric_name: Name of metric to monitor
        threshold: Threshold value to compare against
        operator: Comparison operator
        severity: Alert severity level
        message_template: Optional custom message template
        cooldown_seconds: Minimum seconds between alerts
        enabled: Whether rule is active
    """
    
    def __init__(
        self,
        name: str,
        metric_name: str,
        threshold: float,
        operator: AlertOperator = AlertOperator.GREATER_THAN,
        severity: AlertSeverity = AlertSeverity.WARNING,
        message_template: Optional[str] = None,
        cooldown_seconds: int = 300,  # 5 minutes default
        enabled: bool = True
    ):
        self.name = name
        self.metric_name = metric_name
        self.threshold = threshold
        self.operator = operator
        self.severity = severity
        self.message_template = message_template
        self.cooldown_seconds = cooldown_seconds
        self.enabled = enabled
        self.last_triggered = 0.0
    
    def __repr__(self):
        return f"AlertRule(name={self.name}, metric={self.metric_name}, threshold={self.threshold})"


class Alert:
    """
    Represents a triggered alert.
    
    Attributes:
        rule_name: Name of the rule that triggered
        metric_name: Metric that triggered the alert
        current_value: Current metric value
        threshold: Threshold that was exceeded
        severity: Alert severity
        message: Alert message
        timestamp: When alert was triggered
        metadata: Additional alert metadata
    """
    
    def __init__(
        self,
        rule_name: str,
        metric_name: str,
        current_value: float,
        threshold: float,
        severity: AlertSeverity,
        message: str,
        timestamp: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.rule_name = rule_name
        self.metric_name = metric_name
        self.current_value = current_value
        self.threshold = threshold
        self.severity = severity
        self.message = message
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"Alert({self.severity.value}: {self.rule_name})"


class NotificationHandler:
    """Base class for alert notification handlers."""
    
    def send(self, alert: Alert) -> bool:
        """
        Send alert notification.
        
        Args:
            alert: Alert to send
        
        Returns:
            True if notification was sent successfully
        """
        raise NotImplementedError


class ConsoleHandler(NotificationHandler):
    """
    Console notification handler for testing and debugging.
    
    Prints alerts to stdout with colored formatting.
    """
    
    def send(self, alert: Alert) -> bool:
        """Print alert to console."""
        # Icon for each severity level
        icons = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨"
        }
        
        icon = icons.get(alert.severity, "•")
        
        print(f"\n{icon} ALERT [{alert.severity.value.upper()}] {alert.rule_name}")
        print(f"   Metric: {alert.metric_name}")
        print(f"   Value: {alert.current_value} (threshold: {alert.threshold})")
        print(f"   Message: {alert.message}\n")
        
        return True


class WebhookHandler(NotificationHandler):
    """
    Webhook notification handler.
    
    Sends alerts to a webhook URL (Slack, PagerDuty, custom endpoints, etc.)
    """
    
    def __init__(
        self,
        webhook_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10
    ):
        """
        Initialize webhook handler.
        
        Args:
            webhook_url: URL to send POST requests to
            headers: Optional HTTP headers
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout
    
    def send(self, alert: Alert) -> bool:
        """Send alert via webhook."""
        try:
            import requests
            
            payload = {
                "rule_name": alert.rule_name,
                "metric_name": alert.metric_name,
                "current_value": alert.current_value,
                "threshold": alert.threshold,
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "metadata": alert.metadata
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            
            return response.status_code < 400
            
        except Exception as e:
            print(f"Webhook notification failed: {e}")
            return False


class EmailHandler(NotificationHandler):
    """
    Email notification handler.
    
    Sends alerts via SMTP email.
    """
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        from_email: str,
        to_emails: List[str],
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True
    ):
        """
        Initialize email handler.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            from_email: Sender email address
            to_emails: List of recipient email addresses
            username: Optional SMTP username
            password: Optional SMTP password
            use_tls: Whether to use TLS encryption
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.to_emails = to_emails
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    def send(self, alert: Alert) -> bool:
        """Send alert via email."""
        try:
            import smtplib
            from email.mime.text import MIMEText

            # Create email
            subject = f"[{alert.severity.value.upper()}] {alert.rule_name}"
            body = f"""
Alert Triggered: {alert.rule_name}

Severity: {alert.severity.value}
Metric: {alert.metric_name}
Current Value: {alert.current_value}
Threshold: {alert.threshold}

Message: {alert.message}

Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp))}
"""
            
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Email notification failed: {e}")
            return False


class AnomalyDetector:
    """
    Statistical anomaly detection for metrics.
    
    Uses moving average and standard deviation to detect anomalies.
    """
    
    def __init__(self, window_size: int = 20, threshold_stdevs: float = 3.0):
        """
        Initialize anomaly detector.
        
        Args:
            window_size: Number of recent values to consider
            threshold_stdevs: Number of standard deviations for anomaly
        """
        self.window_size = window_size
        self.threshold_stdevs = threshold_stdevs
        self._history: Dict[str, List[float]] = {}
    
    def check(self, metric_name: str, value: float) -> bool:
        """
        Check if a value is anomalous.
        
        Args:
            metric_name: Name of metric
            value: Current value to check
        
        Returns:
            True if value is anomalous
        """
        if metric_name not in self._history:
            self._history[metric_name] = []
        
        history = self._history[metric_name]
        
        # Need enough history for detection
        if len(history) < self.window_size:
            history.append(value)
            return False
        
        # Calculate statistics
        avg = mean(history)
        std = stdev(history) if len(history) > 1 else 0
        
        # Check if value is anomalous
        is_anomaly = abs(value - avg) > (self.threshold_stdevs * std)
        
        # Update history (sliding window)
        history.append(value)
        if len(history) > self.window_size:
            history.pop(0)
        
        return is_anomaly


class AlertManager:
    """
    Thread-safe singleton alert manager.
    
    Manages alert rules, evaluates metrics, and dispatches notifications.
    
    Example:
        >>> manager = AlertManager.get_instance()
        >>> manager.add_handler(ConsoleHandler())
        >>> rule = AlertRule("high_cpu", "system.cpu_percent", 90.0)
        >>> manager.add_rule(rule)
        >>> manager.check_metrics()
    """
    
    _instance: Optional['AlertManager'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __init__(self):
        """Initialize the alert manager."""
        self._rules: Dict[str, AlertRule] = {}
        self._handlers: List[NotificationHandler] = []
        self._alerts: List[Alert] = []
        self._alert_lock = threading.Lock()
        self._metrics_collector = MetricsCollector.get_instance()
        self._anomaly_detector = AnomalyDetector()
        self._enabled = True
    
    @classmethod
    def get_instance(cls) -> 'AlertManager':
        """
        Get the singleton instance of AlertManager.
        
        Returns:
            The singleton AlertManager instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def enable(self) -> None:
        """Enable alert checking."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable alert checking."""
        self._enabled = False
    
    def add_rule(self, rule: AlertRule) -> None:
        """
        Add an alert rule.
        
        Args:
            rule: AlertRule to add
        """
        with self._alert_lock:
            self._rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str) -> None:
        """
        Remove an alert rule.
        
        Args:
            rule_name: Name of rule to remove
        """
        with self._alert_lock:
            if rule_name in self._rules:
                del self._rules[rule_name]
    
    def get_rule(self, rule_name: str) -> Optional[AlertRule]:
        """
        Get an alert rule by name.
        
        Args:
            rule_name: Name of rule
        
        Returns:
            AlertRule or None if not found
        """
        with self._alert_lock:
            return self._rules.get(rule_name)
    
    def add_handler(self, handler: NotificationHandler) -> None:
        """
        Add a notification handler.
        
        Args:
            handler: NotificationHandler instance
        """
        with self._alert_lock:
            self._handlers.append(handler)
    
    def check_metrics(self) -> List[Alert]:
        """
        Evaluate all rules against current metrics.
        
        Returns:
            List of triggered alerts
        """
        if not self._enabled:
            return []
        
        triggered_alerts = []
        
        with self._alert_lock:
            for rule in self._rules.values():
                # Skip disabled rules
                if not rule.enabled:
                    continue
                
                # Check cooldown period
                if time.time() - rule.last_triggered < rule.cooldown_seconds:
                    continue
                
                # Get current metric value
                metric = self._metrics_collector.get_metric(rule.metric_name)
                if not metric:
                    continue
                
                # Calculate current value (mean for histograms)
                if metric.metric_type == MetricType.HISTOGRAM:
                    if not metric.value:
                        continue
                    current_value = mean(metric.value)
                else:
                    current_value = metric.value
                
                # Evaluate rule
                if self._evaluate_rule(rule, current_value):
                    alert = self._create_alert(rule, current_value)
                    triggered_alerts.append(alert)
                    
                    # Store alert
                    self._alerts.append(alert)
                    
                    # Update last triggered time
                    rule.last_triggered = time.time()
                    
                    # Dispatch notifications
                    for handler in self._handlers:
                        try:
                            handler.send(alert)
                        except Exception as e:
                            print(f"Notification handler error: {e}")
        
        return triggered_alerts
    
    def _evaluate_rule(self, rule: AlertRule, current_value: float) -> bool:
        """
        Evaluate if a rule condition is met.
        
        Args:
            rule: Rule to evaluate
            current_value: Current metric value
        
        Returns:
            True if rule condition is met
        """
        operators = {
            AlertOperator.GREATER_THAN: lambda v, t: v > t,
            AlertOperator.LESS_THAN: lambda v, t: v < t,
            AlertOperator.EQUALS: lambda v, t: v == t,
            AlertOperator.NOT_EQUALS: lambda v, t: v != t,
            AlertOperator.GREATER_EQUAL: lambda v, t: v >= t,
            AlertOperator.LESS_EQUAL: lambda v, t: v <= t,
        }
        
        op_func = operators.get(rule.operator, lambda v, t: False)
        return op_func(current_value, rule.threshold)
    
    def _create_alert(self, rule: AlertRule, current_value: float) -> Alert:
        """
        Create an Alert from a triggered rule.
        
        Args:
            rule: Triggered rule
            current_value: Current metric value
        
        Returns:
            Alert instance
        """
        # Use custom message template if provided
        if rule.message_template:
            message = rule.message_template.format(
                metric=rule.metric_name,
                value=current_value,
                threshold=rule.threshold
            )
        else:
            message = (
                f"{rule.metric_name} is {current_value} "
                f"(threshold: {rule.operator.value} {rule.threshold})"
            )
        
        return Alert(
            rule_name=rule.name,
            metric_name=rule.metric_name,
            current_value=current_value,
            threshold=rule.threshold,
            severity=rule.severity,
            message=message
        )
    
    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        limit: Optional[int] = None
    ) -> List[Alert]:
        """
        Get alert history.
        
        Args:
            severity: Optional filter by severity level
            limit: Optional limit on number of alerts returned
        
        Returns:
            List of Alert objects
        """
        with self._alert_lock:
            alerts = self._alerts.copy()
        
        # Filter by severity
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Sort by timestamp (most recent first)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            alerts = alerts[:limit]
        
        return alerts
    
    def clear_alerts(self) -> None:
        """Clear alert history."""
        with self._alert_lock:
            self._alerts.clear()


def get_alert_manager() -> AlertManager:
    """
    Convenience function to get the AlertManager singleton.
    
    Returns:
        The singleton AlertManager instance
    
    Example:
        >>> from gamma_engine.core.alerting import get_alert_manager, AlertRule
        >>> manager = get_alert_manager()
        >>> manager.add_rule(AlertRule("high_cpu", "system.cpu_percent", 90.0))
    """
    return AlertManager.get_instance()
