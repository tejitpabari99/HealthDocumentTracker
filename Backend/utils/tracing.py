"""
OpenTelemetry tracing configuration for distributed tracing.

Features:
- Trace and span setup for request tracking
- Integration with Azure Monitor
- Automatic Flask instrumentation
- Context propagation across service boundaries
"""

import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: Optional[trace.Tracer] = None

def setup_tracing(app, service_name: str = "HealthDocumentTracker") -> Optional[trace.Tracer]:
    """
    Configure OpenTelemetry tracing for the Flask application.
    
    Args:
        app: Flask application instance
        service_name: Name of the service for tracing
    
    Returns:
        Tracer instance or None if setup fails
    """
    global _tracer
    
    try:
        # Check if tracing is enabled
        enable_tracing = os.getenv('ENABLE_TRACING', 'true').lower() == 'true'
        if not enable_tracing:
            logger.info("Tracing is disabled")
            return None
        
        # Create resource with service information
        resource = Resource.create({
            "service.name": service_name,
            "service.version": os.getenv('SERVICE_VERSION', '1.0.0'),
            "deployment.environment": os.getenv('ENVIRONMENT', 'development')
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        
        # Configure Azure Monitor exporter if connection string is available
        connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
        if connection_string:
            try:
                from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
                
                azure_exporter = AzureMonitorTraceExporter(
                    connection_string=connection_string
                )
                
                # Add span processor with Azure exporter
                tracer_provider.add_span_processor(
                    BatchSpanProcessor(azure_exporter)
                )
                
                logger.info("Azure Monitor trace exporter configured")
            except ImportError:
                logger.warning("Azure Monitor OpenTelemetry exporter not installed")
            except Exception as e:
                logger.error(f"Failed to configure Azure Monitor exporter: {str(e)}")
        
        # Set the tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Instrument Flask application
        FlaskInstrumentor().instrument_app(app)
        logger.info("Flask application instrumented for tracing")
        
        # Create and store tracer
        _tracer = trace.get_tracer(__name__)
        
        logger.info(f"OpenTelemetry tracing initialized for service: {service_name}")
        return _tracer
        
    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not installed: {str(e)}")
        logger.warning("Install with: pip install -r requirements.txt")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {str(e)}")
        return None

def get_tracer() -> Optional[trace.Tracer]:
    """
    Get the global tracer instance.
    
    Returns:
        Tracer instance or None if tracing is not set up
    """
    return _tracer

def create_span(name: str, attributes: Optional[dict] = None):
    """
    Create a new span for tracing operations.
    
    Args:
        name: Name of the span
        attributes: Optional dictionary of attributes to add to the span
    
    Returns:
        Span context manager or dummy context if tracing is disabled
    
    Usage:
        with create_span("database_query", {"query_type": "SELECT"}):
            # Your code here
            pass
    """
    if _tracer is None:
        # Return a dummy context manager if tracing is not enabled
        from contextlib import nullcontext
        return nullcontext()
    
    span = _tracer.start_as_current_span(name)
    
    if attributes and hasattr(span, 'set_attributes'):
        span.set_attributes(attributes)
    
    return span

def add_span_attributes(**kwargs):
    """
    Add attributes to the current active span.
    
    Args:
        **kwargs: Key-value pairs to add as attributes
    
    Usage:
        add_span_attributes(user_id="123", document_count=5)
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attributes(kwargs)

def add_span_event(name: str, attributes: Optional[dict] = None):
    """
    Add an event to the current active span.
    
    Args:
        name: Name of the event
        attributes: Optional dictionary of attributes for the event
    
    Usage:
        add_span_event("cache_hit", {"cache_key": "user:123"})
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.add_event(name, attributes or {})

def set_span_error(exception: Exception):
    """
    Mark the current span as error with exception details.
    
    Args:
        exception: The exception that occurred
    
    Usage:
        try:
            # Your code
            pass
        except Exception as e:
            set_span_error(e)
            raise
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_status(Status(StatusCode.ERROR, str(exception)))
        current_span.record_exception(exception)

def get_trace_context() -> dict:
    """
    Get the current trace context for propagation.
    
    Returns:
        Dictionary with trace_id and span_id
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        span_context = current_span.get_span_context()
        return {
            'trace_id': format(span_context.trace_id, '032x'),
            'span_id': format(span_context.span_id, '016x'),
            'trace_flags': span_context.trace_flags
        }
    return {}
