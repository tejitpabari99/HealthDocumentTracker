"""
Request/Response logging middleware for Flask.

Features:
- Log critical request/response components only
- Request: method, URL, path, userId, content_type, content_length
- Response: status_code, duration_ms, content_type, content_length
- Generate and track correlation IDs with tracing
- Integration with OpenTelemetry spans
- Mask sensitive data in logs
- File upload tracking with size information
"""

import logging
import time
import uuid
import json
from flask import request, g, jsonify
from functools import wraps
from typing import Optional, Dict, Any, List
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

# Import tracing utilities
try:
    from Backend.utils.tracing import add_span_attributes, add_span_event, set_span_error, get_trace_context
    TRACING_ENABLED = True
except ImportError:
    TRACING_ENABLED = False
    logger.warning("Tracing utilities not available")

# Sensitive fields to mask in logs
SENSITIVE_FIELDS = {
    'password', 'token', 'api_key', 'secret', 'authorization',
    'access_token', 'refresh_token', 'ssn', 'credit_card', 'api-key'
}

# Sensitive headers to mask
SENSITIVE_HEADERS = {
    'authorization', 'x-api-key', 'cookie', 'x-auth-token', 'x-access-token'
}

def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking."""
    return str(uuid.uuid4())

def mask_sensitive_data(data: Any, mask_value: str = "***REDACTED***") -> Any:
    """
    Recursively mask sensitive fields in dictionaries.
    
    Args:
        data: Data to mask (dict, list, or primitive)
        mask_value: Value to use for masked fields
    
    Returns:
        Data with sensitive fields masked
    """
    if isinstance(data, dict):
        return {
            key: mask_value if key.lower() in SENSITIVE_FIELDS else mask_sensitive_data(value, mask_value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item, mask_value) for item in data]
    else:
        return data

def mask_headers(headers: Dict[str, str], mask_value: str = "***REDACTED***") -> Dict[str, str]:
    """
    Mask sensitive headers.
    
    Args:
        headers: Headers dictionary
        mask_value: Value to use for masked headers
    
    Returns:
        Headers with sensitive values masked
    """
    return {
        key: mask_value if key.lower() in SENSITIVE_HEADERS else value
        for key, value in headers.items()
    }

def get_file_info(file: FileStorage) -> Dict[str, Any]:
    """
    Extract information about uploaded file.
    
    Args:
        file: FileStorage object
    
    Returns:
        Dictionary with file information
    """
    return {
        'filename': file.filename,
        'content_type': file.content_type,
        'content_length': file.content_length if file.content_length else 'unknown'
    }

def get_request_files() -> Optional[List[Dict[str, Any]]]:
    """
    Extract information about uploaded files.
    
    Returns:
        List of file information dictionaries or None
    """
    if not request.files:
        return None
    
    files_info = []
    for field_name, file in request.files.items():
        if file and file.filename:
            file_info = get_file_info(file)
            file_info['field_name'] = field_name
            files_info.append(file_info)
    
    return files_info if files_info else None

def get_request_data() -> Optional[Dict[str, Any]]:
    """
    Safely extract request data with size limits.
    
    Returns:
        Request data dictionary or None if extraction fails
    """
    try:
        # Check for JSON content
        if request.is_json:
            # Get JSON data with size limit (1MB)
            if request.content_length and request.content_length > 1024 * 1024:
                return {"_note": "Request body too large to log (>1MB)", "size_bytes": request.content_length}
            
            data = request.get_json(silent=True)
            if data:
                # Mask sensitive fields
                return mask_sensitive_data(data)
        
        # Check for form data
        elif request.form:
            form_data = dict(request.form)
            return mask_sensitive_data(form_data)
        
        # Check for raw data (for non-JSON/form requests)
        elif request.data:
            if request.content_length and request.content_length > 1024 * 1024:
                return {"_note": "Request body too large to log (>1MB)", "size_bytes": request.content_length}
            
            # Try to decode as text
            try:
                body_text = request.data.decode('utf-8')
                if len(body_text) > 10000:  # Limit text to 10KB for logging
                    return {"_note": "Request body truncated", "preview": body_text[:10000] + "..."}
                return {"raw_body": body_text}
            except UnicodeDecodeError:
                return {"_note": "Binary data", "size_bytes": len(request.data)}
        
        return None
    except Exception as e:
        logger.debug(f"Failed to extract request data: {str(e)}")
        return None

def log_request():
    """Log critical incoming request details and set up correlation ID with tracing."""
    # Generate correlation ID
    correlation_id = generate_correlation_id()
    g.correlation_id = correlation_id
    g.start_time = time.time()
    
    # Get user_id if available (set by authentication middleware)
    user_id = getattr(g, 'user_id', None)
    
    # Get trace context if tracing is enabled
    trace_context = {}
    if TRACING_ENABLED:
        trace_context = get_trace_context()
        # Add trace context to g for later use
        g.trace_id = trace_context.get('trace_id')
        g.span_id = trace_context.get('span_id')
    
    # Build minimal request details - log only critical components
    request_details = {
        'correlation_id': correlation_id,
        'trace_id': trace_context.get('trace_id'),
        'span_id': trace_context.get('span_id'),
        'method': request.method,
        'url': request.url,
        'path': request.path,
        'user_id': user_id,
        'content_type': request.content_type,
        'content_length': request.content_length
    }
    
    # Add file information if present (critical for file uploads)
    request_files = get_request_files()
    if request_files:
        request_details['uploaded_files'] = request_files
    
    # Add request attributes to current span if tracing is enabled
    if TRACING_ENABLED:
        add_span_attributes(
            correlation_id=correlation_id,
            user_id=user_id or 'anonymous',
            http_method=request.method,
            http_path=request.path,
            http_url=request.url,
            content_type=request.content_type or 'none',
            content_length=request.content_length or 0
        )
    
    # Build log message
    log_extra = {
        'custom_dimensions': request_details
    }
    
    # Log with appropriate detail level
    logger.info(
        f"→ REQUEST: {request.method} {request.path}",
        extra=log_extra
    )

def log_response(response):
    """
    Log critical response details - status code, timing, content metadata.
    Does NOT log response body to avoid over-logging.
    
    Args:
        response: Flask response object
    
    Returns:
        Response object (unmodified)
    """
    # Calculate request duration
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        duration_ms = round(duration * 1000, 2)
    else:
        duration = 0
        duration_ms = 0
    
    # Get correlation ID and trace context
    correlation_id = getattr(g, 'correlation_id', 'unknown')
    trace_id = getattr(g, 'trace_id', None)
    span_id = getattr(g, 'span_id', None)
    user_id = getattr(g, 'user_id', None)
    
    # Determine log level based on status code
    status_code = response.status_code
    if status_code >= 500:
        log_level = logging.ERROR
    elif status_code >= 400:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    
    # Build minimal response details - log only critical components
    response_details = {
        'correlation_id': correlation_id,
        'trace_id': trace_id,
        'span_id': span_id,
        'method': request.method,
        'url': request.url,
        'path': request.path,
        'user_id': user_id,
        'status_code': status_code,
        'duration_ms': duration_ms,
        'response_content_type': response.content_type,
        'response_content_length': response.content_length
    }
    
    # Add response attributes to current span if tracing is enabled
    if TRACING_ENABLED:
        add_span_attributes(
            http_status_code=status_code,
            duration_ms=duration_ms,
            response_content_type=response.content_type or 'none',
            response_content_length=response.content_length or 0
        )
        
        # Add event for status
        if status_code >= 400:
            add_span_event("http_error", {
                "status_code": status_code,
                "path": request.path
            })
    
    # Build log message
    log_extra = {
        'custom_dimensions': response_details
    }
    
    # Create status indicator
    status_indicator = "✓" if status_code < 400 else "✗"
    
    logger.log(
        log_level,
        f"← RESPONSE: {status_indicator} {request.method} {request.path} - {status_code} ({duration_ms}ms)",
        extra=log_extra
    )
    
    # Add correlation and trace IDs to response headers
    response.headers['X-Correlation-ID'] = correlation_id
    if trace_id:
        response.headers['X-Trace-ID'] = trace_id
    if span_id:
        response.headers['X-Span-ID'] = span_id
    
    return response

def extract_user_id():
    """
    Extract user ID from request for authentication.
    Supports multiple methods for development and production.
    
    Development Mode (FLASK_ENV=development):
        - Accepts X-User-Id header
        - Accepts test_user_id query parameter
        - Accepts Authorization header (JWT)
    
    Production Mode:
        - Only accepts Authorization header (JWT)
    
    Sets g.user_id for use in route handlers.
    """
    import os
    from flask import g, request, jsonify
    
    user_id = None
    is_development = os.getenv('FLASK_ENV', 'production').lower() == 'development'
    
    # Priority 1: Authorization header (JWT token)
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            # Extract token from "Bearer <token>" format
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                # TODO: Implement JWT decoding when authentication is added
                logger.warning("JWT decoding not yet implemented - auth disabled")
            else:
                logger.warning(f"Invalid Authorization header format")
        except Exception as e:
            logger.warning(f"Failed to extract user from Authorization header: {str(e)}")
    
    # Priority 2: X-User-Id header (development only)
    if not user_id and is_development:
        user_id = request.headers.get('X-User-Id')
        if user_id:
            logger.debug(f"User ID extracted from X-User-Id header: {user_id}")
    
    # Store user_id in g for access in route handlers
    g.user_id = user_id
    
    # Log authentication attempt
    if user_id:
        logger.debug(f"User authenticated: {user_id}")
    else:
        logger.debug("No user authentication provided")

def require_auth(f):
    """
    Decorator to require authentication for a route.
    
    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user_id = g.user_id  # Access authenticated user ID
            return jsonify({'user_id': user_id})
    
    Returns 401 if no valid user_id is found.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'user_id') or not g.user_id:
            logger.warning(f"Unauthorized access attempt to {request.path}")
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please provide authentication credentials',
                'hint': 'In development: Use X-User-Id header or test_user_id parameter'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def setup_authentication(app):
    """
    Set up authentication middleware for Flask app.
    Extracts user_id from various sources based on environment.
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request_auth():
        """Hook to extract user authentication before processing."""
        extract_user_id()

def setup_request_logging(app):
    """
    Set up request/response logging middleware for Flask app.
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request_logging():
        """Hook to log requests before processing."""
        log_request()
    
    @app.after_request
    def after_request_logging(response):
        """Hook to log responses after processing."""
        return log_response(response)
    
    @app.errorhandler(Exception)
    def log_exception(error):
        """Log unhandled exceptions with full context."""
        correlation_id = getattr(g, 'correlation_id', 'unknown')
        trace_id = getattr(g, 'trace_id', None)
        
        # Mark span as error if tracing is enabled
        if TRACING_ENABLED:
            set_span_error(error)
        
        logger.error(
            f"Unhandled exception: {str(error)}",
            extra={
                'custom_dimensions': {
                    'correlation_id': correlation_id,
                    'trace_id': trace_id,
                    'method': request.method,
                    'path': request.path,
                    'exception_type': type(error).__name__
                }
            },
            exc_info=True
        )
        
        # Re-raise the exception to let Flask handle it
        raise

def with_logging(func):
    """
    Decorator to add function-level logging.
    
    Usage:
        @with_logging
        def my_function():
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_logger = logging.getLogger(func.__module__)
        correlation_id = getattr(g, 'correlation_id', 'unknown')
        
        func_logger.debug(
            f"Entering function: {func.__name__}",
            extra={'custom_dimensions': {'correlation_id': correlation_id}}
        )
        
        try:
            result = func(*args, **kwargs)
            func_logger.debug(
                f"Exiting function: {func.__name__}",
                extra={'custom_dimensions': {'correlation_id': correlation_id}}
            )
            return result
        except Exception as e:
            func_logger.error(
                f"Exception in function {func.__name__}: {str(e)}",
                extra={'custom_dimensions': {'correlation_id': correlation_id}},
                exc_info=True
            )
            raise
    
    return wrapper
