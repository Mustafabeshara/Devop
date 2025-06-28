"""
Audit log model for security and activity tracking
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, String, Integer, Text, ForeignKey, JSON
from enum import Enum

db = SQLAlchemy()

class EventType(Enum):
    """Audit event types"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    
    # User management events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    
    # Session events
    SESSION_CREATED = "session_created"
    SESSION_STARTED = "session_started"
    SESSION_ACCESSED = "session_accessed"
    SESSION_EXTENDED = "session_extended"
    SESSION_STOPPED = "session_stopped"
    SESSION_EXPIRED = "session_expired"
    SESSION_ERROR = "session_error"
    
    # Container events
    CONTAINER_CREATED = "container_created"
    CONTAINER_STARTED = "container_started"
    CONTAINER_STOPPED = "container_stopped"
    CONTAINER_DESTROYED = "container_destroyed"
    CONTAINER_ERROR = "container_error"
    
    # Security events
    SECURITY_VIOLATION = "security_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # Administrative events
    ADMIN_LOGIN = "admin_login"
    ADMIN_ACTION = "admin_action"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    
    # API events
    API_CALL = "api_call"
    API_ERROR = "api_error"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"

class SeverityLevel(Enum):
    """Security event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditLog(db.Model):
    """Audit log model for tracking security and user events"""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Event information
    event_type = db.Column(db.Enum(EventType), nullable=False)
    severity = db.Column(db.Enum(SeverityLevel), default=SeverityLevel.LOW)
    message = db.Column(db.Text)
    description = db.Column(db.Text)
    
    # User and session information
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    session_id = db.Column(db.String(64), nullable=True)
    username = db.Column(db.String(80))  # Store username even if user is deleted
    
    # Request information
    ip_address = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.Text)
    request_method = db.Column(db.String(10))
    request_url = db.Column(db.Text)
    request_headers = db.Column(JSON)
    
    # Response information
    response_status = db.Column(db.Integer)
    response_time_ms = db.Column(db.Integer)
    
    # Additional context
    resource_type = db.Column(db.String(50))  # e.g., 'user', 'session', 'container'
    resource_id = db.Column(db.String(100))   # ID of the affected resource
    old_values = db.Column(JSON)              # Previous values for update events
    new_values = db.Column(JSON)              # New values for update events
    
    # Metadata
    metadata = db.Column(JSON)                # Additional context data
    tags = db.Column(JSON)                    # Tags for categorization
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __init__(self, event_type, **kwargs):
        self.event_type = event_type
        
        # Set default severity based on event type
        self.severity = self._get_default_severity(event_type)
        
        # Apply any additional kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @staticmethod
    def _get_default_severity(event_type):
        """Get default severity level for event type"""
        critical_events = [
            EventType.SECURITY_VIOLATION,
            EventType.UNAUTHORIZED_ACCESS,
            EventType.ACCOUNT_LOCKED,
            EventType.SUSPICIOUS_ACTIVITY
        ]
        
        high_events = [
            EventType.LOGIN_FAILED,
            EventType.RATE_LIMIT_EXCEEDED,
            EventType.CONTAINER_ERROR,
            EventType.SESSION_ERROR,
            EventType.ADMIN_ACTION
        ]
        
        medium_events = [
            EventType.PASSWORD_CHANGE,
            EventType.PASSWORD_RESET,
            EventType.USER_CREATED,
            EventType.USER_DELETED,
            EventType.ADMIN_LOGIN
        ]
        
        if event_type in critical_events:
            return SeverityLevel.CRITICAL
        elif event_type in high_events:
            return SeverityLevel.HIGH
        elif event_type in medium_events:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    @classmethod
    def log_event(cls, event_type, user=None, session_id=None, message=None, 
                  ip_address=None, user_agent=None, request=None, **kwargs):
        """Convenient method to create audit log entries"""
        
        # Extract request information if request object is provided
        if request:
            ip_address = ip_address or request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            user_agent = user_agent or request.headers.get('User-Agent')
            kwargs.update({
                'request_method': request.method,
                'request_url': request.url,
                'request_headers': dict(request.headers)
            })
        
        # Extract user information
        if user:
            kwargs.update({
                'user_id': user.id,
                'username': user.username
            })
        
        # Create audit log entry
        audit_log = cls(
            event_type=event_type,
            message=message,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )
        
        db.session.add(audit_log)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Log to system logger as fallback
            import logging
            logging.error(f"Failed to save audit log: {e}")
        
        return audit_log
    
    @classmethod
    def log_login_success(cls, user, request=None, **kwargs):
        """Log successful login"""
        return cls.log_event(
            EventType.LOGIN_SUCCESS,
            user=user,
            message=f"User {user.username} logged in successfully",
            request=request,
            **kwargs
        )
    
    @classmethod
    def log_login_failed(cls, username, ip_address=None, reason=None, request=None, **kwargs):
        """Log failed login attempt"""
        return cls.log_event(
            EventType.LOGIN_FAILED,
            username=username,
            message=f"Failed login attempt for {username}" + (f": {reason}" if reason else ""),
            ip_address=ip_address,
            request=request,
            **kwargs
        )
    
    @classmethod
    def log_session_event(cls, event_type, session, user=None, message=None, **kwargs):
        """Log session-related events"""
        return cls.log_event(
            event_type,
            user=user,
            session_id=session.id,
            resource_type='session',
            resource_id=session.id,
            message=message or f"Session {session.id} {event_type.value}",
            **kwargs
        )
    
    @classmethod
    def log_security_violation(cls, violation_type, user=None, request=None, **kwargs):
        """Log security violations"""
        return cls.log_event(
            EventType.SECURITY_VIOLATION,
            user=user,
            message=f"Security violation detected: {violation_type}",
            severity=SeverityLevel.CRITICAL,
            request=request,
            metadata={'violation_type': violation_type},
            **kwargs
        )
    
    def to_dict(self):
        """Convert audit log to dictionary for API responses"""
        return {
            'id': self.id,
            'event_type': self.event_type.value if self.event_type else None,
            'severity': self.severity.value if self.severity else None,
            'message': self.message,
            'description': self.description,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'username': self.username,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'request_method': self.request_method,
            'request_url': self.request_url,
            'response_status': self.response_status,
            'response_time_ms': self.response_time_ms,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'metadata': self.metadata,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.event_type.value if self.event_type else "unknown"}>'
