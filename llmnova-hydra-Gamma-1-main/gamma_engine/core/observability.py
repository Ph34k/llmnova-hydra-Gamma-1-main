"""Combined Observability module for Gamma Engine - Metrics, Tracing & Alerting."""
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from enum import Enum
from statistics import mean
from typing import Any, Dict, List, Optional

import psutil


# METRICS
class MetricType(Enum):
    COUNTER="counter";HISTOGRAM="histogram";GAUGE="gauge"

class MetricsCollector:
    _instance=None;_lock=threading.Lock()
    def __init__(self):self._metrics={};self._metric_lock=threading.Lock();self._enabled=True
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:cls._instance=cls()
        return cls._instance
    def enable(self):self._enabled=True
    def disable(self):self._enabled=False
    def reset(self):
        with self._metric_lock:self._metrics.clear()
    def increment(self,name:str,value:float=1.0,labels:Optional[Dict]=None):
        if not self._enabled:return
        key=self._get_key(name,labels)
        with self._metric_lock:
            if key not in self._metrics:self._metrics[key]={"type":MetricType.COUNTER,"value":0.0,"labels":labels or{}}
            self._metrics[key]["value"]+=value;self._metrics[key]["timestamp"]=time.time()
    def record(self,name:str,value:float,labels:Optional[Dict]=None):
        if not self._enabled:return
        key=self._get_key(name,labels)
        with self._metric_lock:
            if key not in self._metrics:self._metrics[key]={"type":MetricType.HISTOGRAM,"value":[],"labels":labels or{}}
            self._metrics[key]["value"].append(value);self._metrics[key]["timestamp"]=time.time()
    def set_gauge(self,name:str,value:float,labels:Optional[Dict]=None):
        if not self._enabled:return
        key=self._get_key(name,labels)
        with self._metric_lock:self._metrics[key]={"type":MetricType.GAUGE,"value":value,"labels":labels or{},"timestamp":time.time()}
    def get_metric(self,name:str,labels:Optional[Dict]=None):
        key=self._get_key(name,labels)
        with self._metric_lock:
            m=self._metrics.get(key)
            if m:
                class M:
                    def __init__(self,d):self.__dict__.update(d);self.metric_type=d["type"]
                return M(m)
    def get_all_metrics(self):
        with self._metric_lock:return self._metrics.copy()
    def collect_system_metrics(self):
        if not self._enabled:return
        try:
            self.set_gauge("system.cpu_percent",psutil.cpu_percent(interval=0.1))
            mem=psutil.virtual_memory();self.set_gauge("system.memory_percent",mem.percent);self.set_gauge("system.memory_mb",mem.used/(1024*1024))
            disk=psutil.disk_usage('/');self.set_gauge("system.disk_percent",disk.percent)
        except:pass
    def export_prometheus(self):
        lines=[]
        with self._metric_lock:
            grouped=defaultdict(list)
            for key,metric in self._metrics.items():
                name=key.split("{")[0]if"{"in key else key;grouped[name].append((key,metric))
            for name,metrics in sorted(grouped.items()):
                prom_name=name.replace(".","_");metric_type=metrics[0][1]["type"].value
                lines.append(f"# HELP {prom_name} {name}");lines.append(f"# TYPE {prom_name} {metric_type}")
                for key,m in metrics:
                    labels_str=self._format_labels(m["labels"])
                    if m["type"]==MetricType.HISTOGRAM:
                        if m["value"]:vals=m["value"];lines.append(f"{prom_name}_count{labels_str} {len(vals)}");lines.append(f"{prom_name}_sum{labels_str} {sum(vals)}")
                    else:lines.append(f"{prom_name}{labels_str} {m['value']}")
                lines.append("")
        return"\n".join(lines)
    def export_json(self):
        with self._metric_lock:return{k:{"type":v["type"].value,"value":v["value"],"labels":v["labels"],"timestamp":v.get("timestamp",0)}for k,v in self._metrics.items()}
    @staticmethod
    def _get_key(name,labels):
        if not labels:return name
        sorted_labels=sorted(labels.items());label_str=",".join(f'{k}="{v}"'for k,v in sorted_labels)
        return f"{name}{{{label_str}}}"
    @staticmethod
    def _format_labels(labels):
        if not labels:return""
        sorted_labels=sorted(labels.items());return"{"+",".join(f'{k}="{v}"'for k,v in sorted_labels)+"}"

def get_metrics_collector():return MetricsCollector.get_instance()

# TRACING
class SpanStatus(Enum):
    OK="ok";ERROR="error";UNSET="unset"

class TracingService:
    _instance: Optional["TracingService"] = None
    _lock = threading.Lock()
    def __init__(self):
        self._enabled: bool = True
        self._spans: List[Dict[str, Any]] = []
        self._span_lock = threading.Lock()
        self._active_spans: Dict[str, Any] = {}
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:cls._instance=cls()
        return cls._instance
    def enable(self):self._enabled=True
    def disable(self):self._enabled=False
    def reset(self):
        with self._span_lock:self._spans.clear();self._active_spans.clear()
    @contextmanager
    def start_span(self,name:str,attributes:Optional[Dict]=None,parent_span_id:Optional[str]=None):
        if not self._enabled:yield SpanContext(None,self);return
        import uuid;span_id=str(uuid.uuid4())[:8];trace_id=str(uuid.uuid4())[:16];start_time=time.time()
        span_ctx=SpanContext(span_id,self,name,attributes or{})
        try:yield span_ctx
        except Exception as e:span_ctx.set_status(SpanStatus.ERROR,str(e));raise
        finally:
            end_time=time.time();duration_ms=(end_time-start_time)*1000
            span_data={"trace_id":trace_id,"span_id":span_id,"parent_span_id":parent_span_id,"name":name,"start_time":start_time,"end_time":end_time,"duration_ms":duration_ms,"attributes":span_ctx._attributes.copy(),"events":span_ctx._events.copy(),"status":span_ctx._status.value,"error":span_ctx._error}
            with self._span_lock:self._spans.append(span_data)
    def get_traces(self,limit:Optional[int]=None):
        with self._span_lock:spans=self._spans.copy()
        spans.sort(key=lambda s:s["start_time"],reverse=True);return spans[:limit]if limit else spans
    def export_traces(self):return self.get_traces()
    def export_trace_tree(self,trace_id:Optional[str]=None):
        spans=self.get_traces()
        if trace_id:spans=[s for s in spans if s["trace_id"]==trace_id]
        if not spans:return"No traces found"
        lines=[]
        for span in spans:
            status_icon="✓"if span["status"]=="ok"else"✗"if span["status"]=="error"else"○"
            lines.append(f"└── {span['name']} ({span['duration_ms']:.1f}ms) {status_icon}")
        return"\n".join(lines)

class SpanContext:
    def __init__(self, span_id: Optional[str], tracer: TracingService, name: str = "", attributes: Optional[Dict[str, Any]] = None):
        self._span_id: Optional[str] = span_id
        self._tracer: TracingService = tracer
        self._name: str = name
        self._attributes: Dict[str, Any] = attributes or {}
        self._events: List[Dict[str, Any]] = []
        self._status: SpanStatus = SpanStatus.UNSET
        self._error: Optional[str] = None

    def set_attribute(self, key: str, value: Any):
        self._attributes[key] = value
        return self

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        self._events.append({"name": name, "timestamp": time.time(), "attributes": attributes or {}})
        return self

    def set_status(self, status: SpanStatus, error: Optional[str] = None):
        self._status = status
        self._error = error
        return self

def get_tracer():return TracingService.get_instance()

# ALERTING
class AlertSeverity(Enum):
    INFO="info";WARNING="warning";ERROR="error";CRITICAL="critical"

class AlertOperator(Enum):
    GREATER_THAN=">";LESS_THAN="<";EQUALS="==";NOT_EQUALS="!=";GREATER_EQUAL=">=";LESS_EQUAL="<="

class AlertRule:
    def __init__(self,name:str,metric_name:str,threshold:float,operator:AlertOperator=AlertOperator.GREATER_THAN,severity:AlertSeverity=AlertSeverity.WARNING,message_template:Optional[str]=None,cooldown_seconds:int=300,enabled:bool=True):self.name=name;self.metric_name=metric_name;self.threshold=threshold;self.operator=operator;self.severity=severity;self.message_template=message_template;self.cooldown_seconds=cooldown_seconds;self.enabled=enabled;self.last_triggered=0.0

class Alert:
    def __init__(self,rule_name:str,metric_name:str,current_value:float,threshold:float,severity:AlertSeverity,message:str,timestamp:float=None,metadata:Optional[Dict]=None):self.rule_name=rule_name;self.metric_name=metric_name;self.current_value=current_value;self.threshold=threshold;self.severity=severity;self.message=message;self.timestamp=timestamp or time.time();self.metadata=metadata or{}

class NotificationHandler:
    def send(self, alert: Alert) -> bool:
        raise NotImplementedError()

class ConsoleHandler(NotificationHandler):
    def send(self,alert:Alert)->bool:
        icons={AlertSeverity.INFO:"ℹ️",AlertSeverity.WARNING:"⚠️",AlertSeverity.ERROR:"❌",AlertSeverity.CRITICAL:"🚨"}
        print(f"\n{icons.get(alert.severity,'•')} ALERT [{alert.severity.value.upper()}] {alert.rule_name}");print(f"   Metric: {alert.metric_name}");print(f"   Value: {alert.current_value} (threshold: {alert.threshold})");print(f"   Message: {alert.message}\n");return True

class WebhookHandler(NotificationHandler):
    def __init__(self,webhook_url:str,headers:Optional[Dict[str,str]]=None,timeout:int=10):self.webhook_url=webhook_url;self.headers=headers or{"Content-Type":"application/json"};self.timeout=timeout
    def send(self,alert:Alert)->bool:
        try:
            import requests;payload={"rule_name":alert.rule_name,"metric_name":alert.metric_name,"current_value":alert.current_value,"threshold":alert.threshold,"severity":alert.severity.value,"message":alert.message,"timestamp":alert.timestamp,"metadata":alert.metadata}
            response=requests.post(self.webhook_url,json=payload,headers=self.headers,timeout=self.timeout);return response.status_code<400
        except Exception as e:print(f"Webhook failed: {e}");return False

class EmailHandler(NotificationHandler):
    def __init__(self,smtp_host:str,smtp_port:int,from_email:str,to_emails:List[str],username:Optional[str]=None,password:Optional[str]=None,use_tls:bool=True):self.smtp_host,self.smtp_port,self.from_email=smtp_host,smtp_port,from_email;self.to_emails,self.username,self.password,self.use_tls=to_emails,username,password,use_tls
    def send(self,alert:Alert)->bool:
        try:
            import smtplib
            from email.mime.text import MIMEText
            subject=f"[{alert.severity.value.upper()}] {alert.rule_name}";body=f"Alert: {alert.rule_name}\nSeverity: {alert.severity.value}\nMetric: {alert.metric_name}\nValue: {alert.current_value}\nThreshold: {alert.threshold}\nMessage: {alert.message}"
            msg=MIMEText(body);msg['Subject'],msg['From'],msg['To']=subject,self.from_email,', '.join(self.to_emails)
            with smtplib.SMTP(self.smtp_host,self.smtp_port)as server:
                if self.use_tls:server.starttls()
                if self.username and self.password:server.login(self.username,self.password)
                server.send_message(msg)
            return True
        except Exception as e:print(f"Email failed: {e}");return False

class AlertManager:
    _instance: Optional["AlertManager"] = None
    _lock = threading.Lock()
    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._handlers: List[NotificationHandler] = []
        self._alerts: List[Alert] = []
        self._alert_lock = threading.Lock()
        self._metrics_collector = MetricsCollector.get_instance()
        self._enabled: bool = True
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:cls._instance=cls()
        return cls._instance
    def enable(self):self._enabled=True
    def disable(self):self._enabled=False
    def add_rule(self,rule:AlertRule):
        with self._alert_lock:self._rules[rule.name]=rule
    def remove_rule(self,rule_name:str):
        with self._alert_lock:
            if rule_name in self._rules:del self._rules[rule_name]
    def get_rule(self,rule_name:str)->Optional[AlertRule]:
        with self._alert_lock:return self._rules.get(rule_name)
    def add_handler(self,handler:NotificationHandler):
        with self._alert_lock:self._handlers.append(handler)
    def check_metrics(self)->List[Alert]:
        if not self._enabled:return[]
        triggered=[]
        with self._alert_lock:
            for rule in self._rules.values():
                if not rule.enabled or time.time()-rule.last_triggered<rule.cooldown_seconds:continue
                metric=self._metrics_collector.get_metric(rule.metric_name)
                if not metric:continue
                current_value=mean(metric.value)if metric.metric_type==MetricType.HISTOGRAM else metric.value
                if self._evaluate(rule,current_value):
                    alert=self._create_alert(rule,current_value);triggered.append(alert);self._alerts.append(alert);rule.last_triggered=time.time()
                    for handler in self._handlers:
                        try:handler.send(alert)
                        except Exception as e:print(f"Handler error: {e}")
        return triggered
    def _evaluate(self,rule,value):
        ops={AlertOperator.GREATER_THAN:lambda v,t:v>t,AlertOperator.LESS_THAN:lambda v,t:v<t,AlertOperator.EQUALS:lambda v,t:v==t,AlertOperator.NOT_EQUALS:lambda v,t:v!=t,AlertOperator.GREATER_EQUAL:lambda v,t:v>=t,AlertOperator.LESS_EQUAL:lambda v,t:v<=t}
        return ops.get(rule.operator,lambda v,t:False)(value,rule.threshold)
    def _create_alert(self,rule,current_value):
        message=rule.message_template.format(metric=rule.metric_name,value=current_value,threshold=rule.threshold)if rule.message_template else f"{rule.metric_name} is {current_value} (threshold: {rule.operator.value} {rule.threshold})"
        return Alert(rule.name,rule.metric_name,current_value,rule.threshold,rule.severity,message)
    def get_alerts(self,severity:Optional[AlertSeverity]=None,limit:Optional[int]=None):
        with self._alert_lock:alerts=self._alerts.copy()
        if severity:alerts=[a for a in alerts if a.severity==severity]
        alerts.sort(key=lambda a:a.timestamp,reverse=True);return alerts[:limit]if limit else alerts
    def clear_alerts(self):
        with self._alert_lock:self._alerts.clear()

def get_alert_manager():return AlertManager.get_instance()
