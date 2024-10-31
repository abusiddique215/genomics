import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
import threading
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from functools import wraps
from .logging import get_logger
from config import config

logger = get_logger('monitoring')

# Metrics
REQUEST_COUNT = Counter(
    'request_total',
    'Total number of requests',
    ['service', 'endpoint', 'method', 'status']
)

REQUEST_LATENCY = Histogram(
    'request_latency_seconds',
    'Request latency in seconds',
    ['service', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

ACTIVE_REQUESTS = Gauge(
    'active_requests',
    'Number of active requests',
    ['service']
)

ERROR_COUNT = Counter(
    'error_total',
    'Total number of errors',
    ['service', 'type']
)

DB_OPERATION_LATENCY = Histogram(
    'db_operation_latency_seconds',
    'Database operation latency in seconds',
    ['service', 'operation'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)

MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    ['service']
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage',
    ['service']
)

@dataclass
class HealthStatus:
    """Health check status"""
    status: str
    details: Dict[str, Any]
    timestamp: datetime

class ServiceMonitor:
    """Service monitoring class"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.health_checks: Dict[str, Callable] = {}
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start Prometheus metrics server"""
        try:
            metrics_port = config.get('monitoring.metrics_port', 9090)
            start_http_server(metrics_port)
            logger.info(f"Started metrics server on port {metrics_port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {str(e)}")
    
    def track_request(self):
        """Decorator to track request metrics"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                ACTIVE_REQUESTS.labels(self.service_name).inc()
                
                try:
                    response = await func(*args, **kwargs)
                    status = response.status_code
                    return response
                except Exception as e:
                    status = 500
                    ERROR_COUNT.labels(self.service_name, type(e).__name__).inc()
                    raise
                finally:
                    ACTIVE_REQUESTS.labels(self.service_name).dec()
                    duration = time.time() - start_time
                    endpoint = func.__name__
                    REQUEST_COUNT.labels(
                        self.service_name, endpoint, 'GET', status
                    ).inc()
                    REQUEST_LATENCY.labels(
                        self.service_name, endpoint
                    ).observe(duration)
            
            return wrapper
        return decorator
    
    def track_db_operation(self):
        """Decorator to track database operation metrics"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    operation = func.__name__
                    DB_OPERATION_LATENCY.labels(
                        self.service_name, operation
                    ).observe(duration)
            return wrapper
        return decorator
    
    def register_health_check(self, name: str, check_func: Callable[[], bool]):
        """Register a health check function"""
        self.health_checks[name] = check_func
    
    async def check_health(self) -> HealthStatus:
        """Run all health checks"""
        details = {}
        overall_status = "healthy"
        
        for name, check_func in self.health_checks.items():
            try:
                is_healthy = await check_func()
                details[name] = {
                    "status": "healthy" if is_healthy else "unhealthy"
                }
                if not is_healthy:
                    overall_status = "unhealthy"
            except Exception as e:
                details[name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_status = "unhealthy"
        
        return HealthStatus(
            status=overall_status,
            details=details,
            timestamp=datetime.utcnow()
        )
    
    def update_resource_metrics(self):
        """Update resource usage metrics"""
        try:
            import psutil
            
            # Update memory usage
            memory = psutil.Process().memory_info()
            MEMORY_USAGE.labels(self.service_name).set(memory.rss)
            
            # Update CPU usage
            cpu_percent = psutil.Process().cpu_percent()
            CPU_USAGE.labels(self.service_name).set(cpu_percent)
            
        except Exception as e:
            logger.error(f"Failed to update resource metrics: {str(e)}")
    
    def start_resource_monitoring(self, interval: int = 60):
        """Start periodic resource monitoring"""
        def monitor():
            while True:
                self.update_resource_metrics()
                time.sleep(interval)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

# Example usage:
# monitor = ServiceMonitor('patient_management')
#
# @monitor.track_request()
# async def get_patient(patient_id: str):
#     return await retrieve_patient(patient_id)
#
# @monitor.track_db_operation()
# async def retrieve_patient(patient_id: str):
#     return await db.get_patient(patient_id)
#
# async def check_db_connection():
#     return await db.ping()
#
# monitor.register_health_check('database', check_db_connection)
# monitor.start_resource_monitoring()
