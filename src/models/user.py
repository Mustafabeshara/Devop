"""
User and Role models for authentication and authorization
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Boolean, DateTime, Column, Integer, String, Text, ForeignKey

db = SQLAlchemy()

# Define models
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    """Role model for user permissions"""
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    permissions = db.Column(db.Text)  # JSON string of permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model, UserMixin):
    """User model with enhanced security features"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    
    # Security fields
    active = db.Column(db.Boolean(), default=True)
    confirmed_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer, default=0)
    
    # Two-factor authentication
    tf_totp_secret = db.Column(db.String(255))
    tf_primary_method = db.Column(db.String(64))
    tf_phone_number = db.Column(db.String(128))
    
    # Account security
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime())
    password_reset_token = db.Column(db.String(255))
    password_reset_expires = db.Column(db.DateTime())
    
    # Profile information
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(255))
    timezone = db.Column(db.String(50), default='UTC')
    
    # Account settings
    max_containers = db.Column(db.Integer, default=3)
    container_timeout = db.Column(db.Integer, default=3600)  # seconds
    preferred_browser = db.Column(db.String(20), default='firefox')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = relationship('Role', secondary=roles_users, 
                        backref=backref('users', lazy='dynamic'))
    browser_sessions = relationship('BrowserSession', backref='user', lazy='dynamic', 
                                  cascade='all, delete-orphan')
    audit_logs = relationship('AuditLog', backref='user', lazy='dynamic')

    @property
    def is_admin(self):
        """Check if user has admin role"""
        return any(role.name == 'admin' for role in self.roles)
    
    @property
    def is_locked(self):
        """Check if account is currently locked"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def lock_account(self, duration_minutes=30):
        """Lock user account for specified duration"""
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts = 0
        db.session.commit()
    
    def unlock_account(self):
        """Unlock user account"""
        self.locked_until = None
        self.failed_login_attempts = 0
        db.session.commit()
    
    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account()
        db.session.commit()
    
    def reset_failed_login(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'timezone': self.timezone,
            'active': self.active,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'login_count': self.login_count,
            'is_admin': self.is_admin,
            'max_containers': self.max_containers,
            'container_timeout': self.container_timeout,
            'preferred_browser': self.preferred_browser,
            'created_at': self.created_at.isoformat(),
            'roles': [role.name for role in self.roles]
        }
    
    def __repr__(self):
        return f'<User {self.email}>'
