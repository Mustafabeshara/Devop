"""
Logging configuration for the Cloud Browser Service
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
import json
import sys

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process',
                          'exc_info', 'exc_text', 'stack_info']:
                log_entry['extra'] = log_entry.get('extra', {})
                log_entry['extra'][key] = value
        
        return json.dumps(log_entry)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Create colored format string
        colored_format = f'{level_color}%(levelname)-8s{reset_color} %(asctime)s [%(name)s:%(lineno)d] %(message)s'
        
        formatter = logging.Formatter(colored_format, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def setup_logging(app):
    """
    Set up comprehensive logging configuration
    
    Args:
        app: Flask application instance
    """
    
    # Get configuration
    log_level = app.config.get('LOG_LEVEL', 'INFO').upper()
    log_dir = Path(app.config.get('LOG_DIR', 'logs'))
    environment = app.config.get('ENV', 'development')
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(exist_ok=True)
    
    # Set root logger level
    logging.root.setLevel(getattr(logging, log_level))
    
    # Clear any existing handlers
    logging.root.handlers.clear()
    
    # Console handler with colored output for development
    console_handler = logging.StreamHandler(sys.stdout)
    if environment == 'development':
        console_handler.setFormatter(ColoredFormatter())
    else:
        console_handler.setFormatter(StructuredFormatter())
    
    console_handler.setLevel(getattr(logging, log_level))
    logging.root.addHandler(console_handler)
    
    # File handler for all logs
    all_logs_file = log_dir / 'app.log'
    file_handler = logging.handlers.RotatingFileHandler(
        all_logs_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(StructuredFormatter())
    file_handler.setLevel(logging.DEBUG)
    logging.root.addHandler(file_handler)
    
    # Error file handler for errors and above
    error_logs_file = log_dir / 'error.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_logs_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setFormatter(StructuredFormatter())
    error_handler.setLevel(logging.ERROR)
    logging.root.addHandler(error_handler)
    
    # Security audit log handler
    security_logs_file = log_dir / 'security.log'
    security_handler = logging.handlers.RotatingFileHandler(
        security_logs_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10  # Keep more security logs
    )
    security_handler.setFormatter(StructuredFormatter())
    security_handler.setLevel(logging.INFO)
    
    # Create security logger
    security_logger = logging.getLogger('security')
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False
    
    # Access log handler for API requests
    access_logs_file = log_dir / 'access.log'
    access_handler = logging.handlers.RotatingFileHandler(
        access_logs_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    access_handler.setFormatter(StructuredFormatter())
    access_handler.setLevel(logging.INFO)
    
    # Create access logger
    access_logger = logging.getLogger('access')
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    
    # Configure specific loggers
    configure_application_loggers(log_level)
    
    # Configure third-party loggers
    configure_third_party_loggers()
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, Environment: {environment}")
    logger.info(f"Log files location: {log_dir.absolute()}")

def configure_application_loggers(log_level):
    """Configure application-specific loggers"""
    
    # Main application logger
    app_logger = logging.getLogger('cloud_browser')
    app_logger.setLevel(getattr(logging, log_level))
    
    # API loggers
    api_logger = logging.getLogger('cloud_browser.api')
    api_logger.setLevel(getattr(logging, log_level))
    
    # Service loggers
    docker_logger = logging.getLogger('cloud_browser.services.docker')
    docker_logger.setLevel(getattr(logging, log_level))
    
    kimi_logger = logging.getLogger('cloud_browser.services.kimi')
    kimi_logger.setLevel(getattr(logging, log_level))
    
    user_logger = logging.getLogger('cloud_browser.services.user')
    user_logger.setLevel(getattr(logging, log_level))
    
    # Auth logger
    auth_logger = logging.getLogger('cloud_browser.auth')
    auth_logger.setLevel(getattr(logging, log_level))
    
    # Database logger
    db_logger = logging.getLogger('cloud_browser.database')
    db_logger.setLevel(getattr(logging, log_level))

def configure_third_party_loggers():
    """Configure third-party library loggers"""
    
    # Werkzeug (Flask development server)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
    
    # SQLAlchemy
    sqlalchemy_logger = logging.getLogger('sqlalchemy')
    sqlalchemy_logger.setLevel(logging.WARNING)
    
    # SQLAlchemy Engine (SQL queries)
    sqlalchemy_engine_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_engine_logger.setLevel(logging.WARNING)
    
    # Docker library
    docker_logger = logging.getLogger('docker')
    docker_logger.setLevel(logging.WARNING)
    
    # Requests library
    requests_logger = logging.getLogger('requests')
    requests_logger.setLevel(logging.WARNING)
    
    # urllib3 (used by requests)
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.WARNING)

def get_logger(name):
    """
    Get a logger with the application namespace
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f'cloud_browser.{name}')

def log_request(request, response, duration_ms=None):
    """
    Log HTTP request details
    
    Args:
        request: Flask request object
        response: Flask response object
        duration_ms: Request duration in milliseconds
    """
    access_logger = logging.getLogger('access')
    
    log_data = {
        'method': request.method,
        'url': request.url,
        'endpoint': request.endpoint,
        'remote_addr': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
        'user_agent': request.headers.get('User-Agent'),
        'status_code': response.status_code,
        'content_length': response.content_length
    }
    
    if duration_ms is not None:
        log_data['duration_ms'] = duration_ms
    
    # Add user info if available
    from flask import g
    if hasattr(g, 'current_user') and g.current_user:
        log_data['user_id'] = g.current_user.id
        log_data['username'] = g.current_user.username
    
    access_logger.info('HTTP Request', extra=log_data)

def log_security_event(event_type, user_id=None, ip_address=None, details=None):
    """
    Log security-related events
    
    Args:
        event_type: Type of security event
        user_id: User ID if applicable
        ip_address: Client IP address
        details: Additional event details
    """
    security_logger = logging.getLogger('security')
    
    log_data = {
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': ip_address,
        'details': details or {}
    }
    
    security_logger.warning(f'Security Event: {event_type}', extra=log_data)

# Context manager for timed operations
class LoggedOperation:
    """Context manager for logging timed operations"""
    
    def __init__(self, operation_name, logger=None):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger('cloud_browser')
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.info(f'Starting operation: {self.operation_name}')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        
        if exc_type is None:
            self.logger.info(
                f'Completed operation: {self.operation_name}',
                extra={'duration_ms': duration}
            )
        else:
            self.logger.error(
                f'Failed operation: {self.operation_name}',
                extra={'duration_ms': duration, 'error': str(exc_val)}
            )
