"""
Centralized logging configuration for the application.

Features:
- Environment-aware setup (local vs Azure)
- Timestamped log files per session
- Console logging with colors (DEBUG level)
- File logging (INFO level)
- Azure Application Insights integration
- Structured logging with correlation IDs
"""

import logging
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# Color codes for console output
class LogColors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Log level colors
    DEBUG = '\033[36m'      # Cyan
    INFO = '\033[32m'       # Green
    WARNING = '\033[33m'    # Yellow
    ERROR = '\033[31m'      # Red
    CRITICAL = '\033[35m'   # Magenta

class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    FORMATS = {
        logging.DEBUG: f"{LogColors.DEBUG}%(asctime)s - %(name)s - [DEBUG] - %(message)s{LogColors.RESET}",
        logging.INFO: f"{LogColors.INFO}%(asctime)s - %(name)s - [INFO] - %(message)s{LogColors.RESET}",
        logging.WARNING: f"{LogColors.WARNING}%(asctime)s - %(name)s - [WARNING] - %(message)s{LogColors.RESET}",
        logging.ERROR: f"{LogColors.ERROR}%(asctime)s - %(name)s - [ERROR] - %(message)s{LogColors.RESET}",
        logging.CRITICAL: f"{LogColors.CRITICAL}%(asctime)s - %(name)s - [CRITICAL] - %(message)s{LogColors.RESET}",
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        formatted = formatter.format(record)
        
        # Add custom_dimensions if present
        if hasattr(record, 'custom_dimensions') and record.custom_dimensions:
            try:
                custom_dims_json = json.dumps(record.custom_dimensions, indent=2, default=str)
                formatted += f"\n{LogColors.BOLD}Custom Dimensions:{LogColors.RESET}\n{custom_dims_json}"
            except Exception as e:
                formatted += f"\n{LogColors.BOLD}Custom Dimensions (serialization failed):{LogColors.RESET} {record.custom_dimensions}"
        
        return formatted

class FileFormatter(logging.Formatter):
    """Standard formatter for file output."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record):
        formatted = super().format(record)
        
        # Add custom_dimensions if present
        if hasattr(record, 'custom_dimensions') and record.custom_dimensions:
            try:
                custom_dims_json = json.dumps(record.custom_dimensions, indent=2, default=str)
                formatted += f"\nCustom Dimensions:\n{custom_dims_json}"
            except Exception as e:
                formatted += f"\nCustom Dimensions (serialization failed): {record.custom_dimensions}"
        
        return formatted

def get_log_filename() -> str:
    """
    Generate a timestamped log filename for the current session.
    
    Returns:
        Filename in format: app_YYYY-MM-DD_HH-MM-SS.log
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f"app_{timestamp}.log"

def setup_logging(
    console_level: Optional[str] = None,
    file_level: Optional[str] = None,
    enable_app_insights: Optional[bool] = None
) -> logging.Logger:
    """
    Configure application-wide logging.
    
    Args:
        console_level: Log level for console output (default: DEBUG)
        file_level: Log level for file output (default: INFO)
        enable_app_insights: Enable Azure App Insights (default: auto-detect)
    
    Returns:
        Root logger instance
    """
    # Get configuration from environment or use defaults
    console_level = console_level or os.getenv('LOG_LEVEL', 'DEBUG').upper()
    file_level = file_level or os.getenv('FILE_LOG_LEVEL', 'INFO').upper()
    
    # Auto-detect App Insights if not specified
    if enable_app_insights is None:
        app_insights_enabled = os.getenv('ENABLE_APP_INSIGHTS', 'true').lower() == 'true'
        has_connection_string = bool(os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING'))
        enable_app_insights = app_insights_enabled and has_connection_string
    
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all logs, handlers will filter
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Suppress noisy third-party loggers
    logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
    logging.getLogger('azure.cosmos').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Console Handler - with colors and DEBUG level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level, logging.DEBUG))
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)
    
    # File Handler - timestamped, INFO level
    log_filename = get_log_filename()
    log_filepath = logs_dir / log_filename
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(getattr(logging, file_level, logging.INFO))
    file_handler.setFormatter(FileFormatter())
    root_logger.addHandler(file_handler)
    
    # Azure Application Insights Handler (via OpenTelemetry)
    # Note: Telemetry is now handled by OpenTelemetry tracing setup
    # See Backend/utils/tracing.py for Azure Monitor integration
    if enable_app_insights:
        connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
        if connection_string:
            root_logger.info(
                "Azure Application Insights configured via OpenTelemetry",
                extra={
                    'custom_dimensions': {
                        'log_file': str(log_filepath),
                        'environment': os.getenv('ENVIRONMENT', 'development')
                    }
                }
            )
        else:
            root_logger.info("Azure Application Insights connection string not found")
    
    # Log the logging configuration
    root_logger.info(
        f"Logging initialized - Console: {console_level}, File: {file_level}, "
        f"Log file: {log_filename}, App Insights: {enable_app_insights}"
    )
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

# Context managers for adding custom dimensions to logs
class LogContext:
    """Context manager for adding custom dimensions to all logs within the context."""
    
    def __init__(self, **kwargs):
        self.custom_dimensions = kwargs
        self.logger = logging.getLogger()
    
    def __enter__(self):
        # Store original factory
        self.original_factory = logging.getLogRecordFactory()
        
        # Create new factory that adds custom dimensions
        def record_factory(*args, **kwargs):
            record = self.original_factory(*args, **kwargs)
            if not hasattr(record, 'custom_dimensions'):
                record.custom_dimensions = {}
            record.custom_dimensions.update(self.custom_dimensions)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original factory
        logging.setLogRecordFactory(self.original_factory)
