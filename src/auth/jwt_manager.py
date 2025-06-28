"""
JWT token management for authentication
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from flask import current_app
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, get_jwt, get_jwt_identity
import redis
import json

class JWTManager:
    """Enhanced JWT token management with blacklisting and additional security"""
    
    def __init__(self, app=None):
        self.app = app
        self.jwt = JWTManager()
        self._redis_client = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize JWT manager with Flask app"""
        self.app = app
        self.jwt.init_app(app)
        
        # Set up JWT configuration
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=1))
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30))
        app.config.setdefault('JWT_BLACKLIST_ENABLED', True)
        app.config.setdefault('JWT_BLACKLIST_TOKEN_CHECKS', ['access', 'refresh'])
        
        # Register JWT callbacks
        self._register_callbacks()
        
        # Initialize Redis for token blacklisting
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection for token blacklisting"""
        try:
            redis_url = self.app.config.get('REDIS_URL')
            if redis_url:
                self._redis_client = redis.from_url(redis_url)
            else:
                # Use in-memory fallback if Redis is not available
                self._redis_client = None
        except Exception:
            self._redis_client = None
    
    def _register_callbacks(self):
        """Register JWT callbacks"""
        
        @self.jwt.token_in_blocklist_loader
        def check_if_token_revoked(jwt_header, jwt_payload):
            """Check if token is blacklisted"""
            return self.is_token_blacklisted(jwt_payload['jti'])
        
        @self.jwt.user_identity_loader
        def user_identity_lookup(user):
            """Set user identity for JWT"""
            if hasattr(user, 'id'):
                return user.id
            return user
        
        @self.jwt.user_lookup_loader
        def user_lookup_callback(_jwt_header, jwt_data):
            """Load user from JWT data"""
            from ..models.user import User
            identity = jwt_data["sub"]
            return User.query.filter_by(id=identity).one_or_none()
        
        @self.jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            """Handle expired tokens"""
            return {
                'error': 'token_expired',
                'message': 'The token has expired'
            }, 401
        
        @self.jwt.invalid_token_loader
        def invalid_token_callback(error):
            """Handle invalid tokens"""
            return {
                'error': 'invalid_token',
                'message': 'Invalid token'
            }, 401
        
        @self.jwt.unauthorized_loader
        def missing_token_callback(error):
            """Handle missing tokens"""
            return {
                'error': 'missing_token',
                'message': 'Authorization token is required'
            }, 401
        
        @self.jwt.revoked_token_loader
        def revoked_token_callback(jwt_header, jwt_payload):
            """Handle revoked tokens"""
            return {
                'error': 'token_revoked',
                'message': 'The token has been revoked'
            }, 401
    
    def create_tokens(self, user, additional_claims: Dict[str, Any] = None) -> Dict[str, str]:
        """Create access and refresh tokens for user"""
        additional_claims = additional_claims or {}
        
        # Add user information to claims
        additional_claims.update({
            'username': user.username,
            'email': user.email,
            'roles': [role.name for role in user.roles],
            'is_admin': user.is_admin,
            'last_login': user.last_login_at.isoformat() if user.last_login_at else None
        })
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        
        refresh_token = create_refresh_token(
            identity=user.id,
            additional_claims={'username': user.username, 'email': user.email}
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': int(self.app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
        }
    
    def blacklist_token(self, jti: str, token_type: str = 'access') -> bool:
        """Add token to blacklist"""
        if not self._redis_client:
            # Use in-memory storage as fallback
            if not hasattr(self.app, '_jwt_blacklist'):
                self.app._jwt_blacklist = set()
            self.app._jwt_blacklist.add(jti)
            return True
        
        try:
            # Store in Redis with expiration
            expiry_time = self.app.config['JWT_ACCESS_TOKEN_EXPIRES']
            if token_type == 'refresh':
                expiry_time = self.app.config['JWT_REFRESH_TOKEN_EXPIRES']
            
            self._redis_client.setex(
                f"blacklist:{jti}",
                int(expiry_time.total_seconds()),
                "blacklisted"
            )
            return True
        except Exception:
            return False
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        if not self._redis_client:
            # Check in-memory storage
            return jti in getattr(self.app, '_jwt_blacklist', set())
        
        try:
            return self._redis_client.exists(f"blacklist:{jti}") > 0
        except Exception:
            return False
    
    def revoke_user_tokens(self, user_id: int) -> bool:
        """Revoke all tokens for a specific user"""
        if not self._redis_client:
            # For in-memory storage, we can't efficiently revoke all user tokens
            return False
        
        try:
            # Add user to revoked users list
            self._redis_client.setex(
                f"revoked_user:{user_id}",
                int(self.app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds()),
                "revoked"
            )
            return True
        except Exception:
            return False
    
    def is_user_tokens_revoked(self, user_id: int) -> bool:
        """Check if all user tokens are revoked"""
        if not self._redis_client:
            return False
        
        try:
            return self._redis_client.exists(f"revoked_user:{user_id}") > 0
        except Exception:
            return False
    
    def get_current_user_claims(self) -> Dict[str, Any]:
        """Get claims from current JWT token"""
        try:
            claims = get_jwt()
            return claims
        except Exception:
            return {}
    
    def get_current_user_id(self) -> Optional[int]:
        """Get current user ID from JWT token"""
        try:
            return get_jwt_identity()
        except Exception:
            return None
    
    def validate_token_claims(self, required_roles: list = None, 
                            required_permissions: list = None) -> bool:
        """Validate current token has required roles/permissions"""
        try:
            claims = self.get_current_user_claims()
            user_roles = claims.get('roles', [])
            
            # Check if user is admin (admin bypasses all checks)
            if claims.get('is_admin', False):
                return True
            
            # Check required roles
            if required_roles:
                if not any(role in user_roles for role in required_roles):
                    return False
            
            # Check required permissions (implement based on your permission system)
            if required_permissions:
                # This would need to be implemented based on your permission model
                pass
            
            return True
        except Exception:
            return False
    
    def refresh_access_token(self, user) -> Dict[str, str]:
        """Create new access token from refresh token"""
        # Get additional claims
        additional_claims = {
            'username': user.username,
            'email': user.email,
            'roles': [role.name for role in user.roles],
            'is_admin': user.is_admin,
            'last_login': user.last_login_at.isoformat() if user.last_login_at else None
        }
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        
        return {
            'access_token': access_token,
            'expires_in': int(self.app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
        }
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens from blacklist (maintenance task)"""
        if not self._redis_client:
            return
        
        # Redis automatically handles expiration, so no cleanup needed
        # This method exists for compatibility with other storage backends
        pass

# Global JWT manager instance
jwt_manager = JWTManager()
