"""
Browser session model for tracking Docker containers and user sessions
"""
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime, String, Integer, Text, ForeignKey, JSON
from enum import Enum

db = SQLAlchemy()

class SessionStatus(Enum):
    """Browser session status enumeration"""
    CREATING = "creating"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    EXPIRED = "expired"

class BrowserType(Enum):
    """Browser type enumeration"""
    FIREFOX = "firefox"
    CHROME = "chrome"
    CHROMIUM = "chromium"

class BrowserSession(db.Model):
    """Browser session model for tracking Docker containers"""
    __tablename__ = 'browser_session'
    
    id = db.Column(db.String(64), primary_key=True)  # Container ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Session information
    session_name = db.Column(db.String(100))
    browser_type = db.Column(db.Enum(BrowserType), default=BrowserType.FIREFOX)
    status = db.Column(db.Enum(SessionStatus), default=SessionStatus.CREATING)
    
    # Container details
    container_id = db.Column(db.String(64), unique=True)
    container_name = db.Column(db.String(100))
    docker_image = db.Column(db.String(100))
    
    # Network and access
    vnc_port = db.Column(db.Integer)
    web_port = db.Column(db.Integer)
    vnc_password = db.Column(db.String(20))
    access_url = db.Column(db.String(255))
    
    # Resource configuration
    cpu_limit = db.Column(db.Float, default=1.0)
    memory_limit = db.Column(db.String(10), default='2g')
    storage_limit = db.Column(db.String(10), default='10g')
    
    # Session lifecycle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    stopped_at = db.Column(db.DateTime)
    
    # Session metadata
    initial_url = db.Column(db.Text)
    user_agent = db.Column(db.String(255))
    screen_resolution = db.Column(db.String(20), default='1920x1080')
    
    # Statistics
    page_views = db.Column(db.Integer, default=0)
    data_transferred = db.Column(db.BigInteger, default=0)  # bytes
    session_duration = db.Column(db.Integer, default=0)  # seconds
    
    # Configuration
    settings = db.Column(JSON)  # JSON field for custom settings
    environment_vars = db.Column(JSON)  # Environment variables for container
    
    # Error tracking
    error_message = db.Column(db.Text)
    error_count = db.Column(db.Integer, default=0)
    last_error_at = db.Column(db.DateTime)
    
    def __init__(self, user_id, browser_type=BrowserType.FIREFOX, session_name=None, **kwargs):
        self.user_id = user_id
        self.browser_type = browser_type
        self.session_name = session_name or f"{browser_type.value}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        # Set expiration time (default 1 hour from now)
        self.expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Apply any additional kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_active(self):
        """Check if session is currently active"""
        return self.status in [SessionStatus.CREATING, SessionStatus.RUNNING]
    
    @property
    def is_expired(self):
        """Check if session has expired"""
        return datetime.utcnow() > self.expires_at if self.expires_at else False
    
    @property
    def time_remaining(self):
        """Get remaining time before session expires"""
        if not self.expires_at:
            return None
        remaining = self.expires_at - datetime.utcnow()
        return max(remaining.total_seconds(), 0)
    
    @property
    def uptime(self):
        """Get session uptime in seconds"""
        if not self.started_at:
            return 0
        end_time = self.stopped_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    def extend_session(self, hours=1):
        """Extend session expiration time"""
        if self.expires_at:
            self.expires_at = max(self.expires_at, datetime.utcnow()) + timedelta(hours=hours)
        else:
            self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        db.session.commit()
    
    def update_last_accessed(self):
        """Update last accessed timestamp"""
        self.last_accessed = datetime.utcnow()
        db.session.commit()
    
    def increment_page_views(self):
        """Increment page view counter"""
        self.page_views += 1
        self.update_last_accessed()
    
    def add_error(self, error_message):
        """Add error message and increment error count"""
        self.error_message = error_message
        self.error_count += 1
        self.last_error_at = datetime.utcnow()
        if self.error_count >= 5:  # Auto-stop after too many errors
            self.status = SessionStatus.ERROR
        db.session.commit()
    
    def clear_errors(self):
        """Clear error information"""
        self.error_message = None
        self.error_count = 0
        self.last_error_at = None
        db.session.commit()
    
    def update_status(self, status, error_message=None):
        """Update session status"""
        self.status = status
        
        if status == SessionStatus.RUNNING and not self.started_at:
            self.started_at = datetime.utcnow()
        elif status in [SessionStatus.STOPPED, SessionStatus.ERROR, SessionStatus.EXPIRED]:
            self.stopped_at = datetime.utcnow()
            if self.started_at:
                self.session_duration = int(self.uptime)
        
        if error_message:
            self.add_error(error_message)
        elif status == SessionStatus.RUNNING:
            self.clear_errors()
        
        db.session.commit()
    
    def to_dict(self):
        """Convert session to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_name': self.session_name,
            'browser_type': self.browser_type.value if self.browser_type else None,
            'status': self.status.value if self.status else None,
            'container_id': self.container_id,
            'container_name': self.container_name,
            'docker_image': self.docker_image,
            'vnc_port': self.vnc_port,
            'web_port': self.web_port,
            'access_url': self.access_url,
            'cpu_limit': self.cpu_limit,
            'memory_limit': self.memory_limit,
            'storage_limit': self.storage_limit,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'stopped_at': self.stopped_at.isoformat() if self.stopped_at else None,
            'initial_url': self.initial_url,
            'screen_resolution': self.screen_resolution,
            'page_views': self.page_views,
            'data_transferred': self.data_transferred,
            'session_duration': self.session_duration,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'time_remaining': self.time_remaining,
            'uptime': self.uptime,
            'error_message': self.error_message,
            'error_count': self.error_count,
            'settings': self.settings
        }
    
    def __repr__(self):
        return f'<BrowserSession {self.id} ({self.browser_type.value if self.browser_type else "unknown"})>'
