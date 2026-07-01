"""
Production Error Handling & Resilience System
Provides graceful degradation, retry logic, and comprehensive error recovery

Features:
- Automatic retry with exponential backoff
- Circuit breaker pattern for failing services
- Graceful degradation strategies
- Comprehensive error logging
- Health monitoring
"""

import logging
import time
import functools
from typing import Callable, Any, Optional, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"  # Minor issue, system continues normally
    MEDIUM = "medium"  # Degraded performance, workaround applied
    HIGH = "high"  # Significant issue, fallback used
    CRITICAL = "critical"  # System failure, emergency mode


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures
    Opens circuit after consecutive failures, closes after cooldown
    """

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""

        # Check if circuit should be closed
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker HALF_OPEN for {func.__name__}")
            else:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")

        try:
            result = func(*args, **kwargs)

            # Success - reset failures
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
                logger.info(f"Circuit breaker CLOSED for {func.__name__}")

            return result

        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()

            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit breaker OPEN for {func.__name__} (failures: {self.failures})")

            raise


def retry_with_backoff(max_retries: int = 3,
                      base_delay: float = 1.0,
                      max_delay: float = 10.0,
                      exponential: bool = True):
    """
    Decorator for automatic retry with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential: Use exponential backoff if True, linear if False
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise

                    # Calculate delay
                    if exponential:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                    else:
                        delay = min(base_delay * (attempt + 1), max_delay)

                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise

                    # Calculate delay
                    if exponential:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                    else:
                        delay = min(base_delay * (attempt + 1), max_delay)

                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)

            raise last_exception

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def safe_execute(func: Callable,
                fallback_value: Any = None,
                log_errors: bool = True) -> Any:
    """
    Execute function safely with fallback

    Args:
        func: Function to execute
        fallback_value: Value to return if function fails
        log_errors: Whether to log errors

    Returns:
        Function result or fallback value
    """

    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"Safe execution failed for {func.__name__}: {e}")
        return fallback_value


class GracefulDegradation:
    """
    Provides fallback strategies when primary systems fail
    """

    @staticmethod
    def get_retrieval_fallback(query: str) -> Dict[str, Any]:
        """Fallback response when retrieval fails"""
        return {
            'answer': "I'm having trouble accessing the knowledge base right now. Please try again in a moment, or rephrase your question.",
            'response': "I'm having trouble accessing the knowledge base right now. Please try again in a moment, or rephrase your question.",
            'confidence': 0.1,
            'intent': 'ERROR_RETRIEVAL',
            'sources': [],
            'degraded': True
        }

    @staticmethod
    def get_llm_fallback(query: str, retrieved_docs: list = None) -> Dict[str, Any]:
        """Fallback response when LLM generation fails"""

        if retrieved_docs and len(retrieved_docs) > 0:
            # Try to use first chunk directly as fallback
            first_chunk = retrieved_docs[0].get('content', '')[:300]
            answer = f"Based on available information: {first_chunk}..."

            return {
                'answer': answer,
                'response': answer,
                'confidence': 0.4,
                'intent': 'DEGRADED_MODE',
                'sources': ['Knowledge Base'],
                'degraded': True
            }
        else:
            return {
                'answer': "I'm experiencing technical difficulties generating a response. Please try rephrasing your question.",
                'response': "I'm experiencing technical difficulties generating a response. Please try rephrasing your question.",
                'confidence': 0.1,
                'intent': 'ERROR_GENERATION',
                'sources': [],
                'degraded': True
            }

    @staticmethod
    def get_memory_fallback() -> Dict[str, Any]:
        """Fallback context when memory fails"""
        return {
            'user_name': None,
            'has_history': False,
            'interaction_count': 0,
            'greeted': False,
            'recent_topics': [],
            'last_topic': None,
            'degraded': True
        }

    @staticmethod
    def get_embedding_fallback(query: str) -> list:
        """Fallback when embedding generation fails - use keyword search only"""
        logger.warning("Embedding generation failed - falling back to keyword search")
        return []  # Empty embedding triggers keyword-only search


class HealthMonitor:
    """
    Monitors system health and component availability
    """

    def __init__(self):
        self.component_status = {}
        self.component_failures = {}

    def register_component(self, name: str):
        """Register a component for monitoring"""
        self.component_status[name] = "HEALTHY"
        self.component_failures[name] = 0

    def report_success(self, component: str):
        """Report successful operation"""
        if component in self.component_status:
            self.component_status[component] = "HEALTHY"
            self.component_failures[component] = 0

    def report_failure(self, component: str, error: Exception):
        """Report component failure"""
        if component not in self.component_failures:
            self.component_failures[component] = 0

        self.component_failures[component] += 1

        if self.component_failures[component] >= 5:
            self.component_status[component] = "UNHEALTHY"
            logger.error(f"❌ Component {component} marked UNHEALTHY after {self.component_failures[component]} failures")
        elif self.component_failures[component] >= 3:
            self.component_status[component] = "DEGRADED"
            logger.warning(f"⚠️ Component {component} marked DEGRADED after {self.component_failures[component]} failures")

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""

        unhealthy = [k for k, v in self.component_status.items() if v == "UNHEALTHY"]
        degraded = [k for k, v in self.component_status.items() if v == "DEGRADED"]

        if unhealthy:
            overall_status = "UNHEALTHY"
        elif degraded:
            overall_status = "DEGRADED"
        else:
            overall_status = "HEALTHY"

        return {
            'overall_status': overall_status,
            'components': self.component_status,
            'failures': self.component_failures,
            'unhealthy_components': unhealthy,
            'degraded_components': degraded
        }

    def is_component_healthy(self, component: str) -> bool:
        """Check if specific component is healthy"""
        return self.component_status.get(component, "UNKNOWN") == "HEALTHY"


# Global health monitor instance
_health_monitor = None


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()

        # Register critical components
        _health_monitor.register_component("retriever")
        _health_monitor.register_component("llm")
        _health_monitor.register_component("memory")
        _health_monitor.register_component("embeddings")

    return _health_monitor


# Convenience functions
def log_error(component: str,
             error: Exception,
             severity: ErrorSeverity = ErrorSeverity.MEDIUM,
             context: Optional[Dict] = None):
    """
    Standardized error logging

    Args:
        component: Component where error occurred
        error: Exception object
        severity: Error severity level
        context: Additional context information
    """

    context_str = f" | Context: {context}" if context else ""

    log_message = f"[{severity.value.upper()}] {component}: {str(error)}{context_str}"

    if severity == ErrorSeverity.CRITICAL:
        logger.critical(log_message, exc_info=True)
    elif severity == ErrorSeverity.HIGH:
        logger.error(log_message, exc_info=True)
    elif severity == ErrorSeverity.MEDIUM:
        logger.warning(log_message)
    else:
        logger.info(log_message)

    # Report to health monitor
    health_monitor = get_health_monitor()
    health_monitor.report_failure(component, error)


def log_success(component: str, message: str = "Operation successful"):
    """Log successful operation and update health status"""
    logger.debug(f"[SUCCESS] {component}: {message}")

    health_monitor = get_health_monitor()
    health_monitor.report_success(component)


# Testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test retry decorator
    @retry_with_backoff(max_retries=3, base_delay=0.5)
    def flaky_function(fail_count: int):
        """Simulates flaky function that fails first N times"""
        if not hasattr(flaky_function, 'attempt'):
            flaky_function.attempt = 0

        flaky_function.attempt += 1

        if flaky_function.attempt <= fail_count:
            raise Exception(f"Intentional failure {flaky_function.attempt}")

        return "Success!"

    print("\n=== Testing Retry Logic ===")
    try:
        result = flaky_function(2)  # Fails 2 times, succeeds on 3rd
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")

    # Test health monitor
    print("\n=== Testing Health Monitor ===")
    monitor = get_health_monitor()

    # Simulate some failures
    monitor.report_failure("retriever", Exception("Connection timeout"))
    monitor.report_failure("retriever", Exception("Connection timeout"))
    monitor.report_failure("retriever", Exception("Connection timeout"))

    health = monitor.get_system_health()
    print(f"System health: {health['overall_status']}")
    print(f"Components: {health['components']}")

    # Simulate recovery
    monitor.report_success("retriever")
    health = monitor.get_system_health()
    print(f"After recovery: {health['overall_status']}")
