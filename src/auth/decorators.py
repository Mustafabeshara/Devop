"""
Authentication decorators for protecting routes
"""
from functools import wraps
from typing import List, Optional, Callable
from flask import request, jsonify, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import time

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

def auth_required(optional: bool = False):
    """
    Authentication decorator with optional mode
    
    Args:
        optional: If True, authentication is optional but user info is loaded if present
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if optional:
                # Optional authentication
                try:
                    from flask_jwt_extended import verify_jwt_in_request
                    verify_jwt_in_request(optional=True)
                    g.current_user_id = get_jwt_identity()
                    g.current_user_claims = get_jwt()
                except Exception:
                    g.current_user_id = None
                    g.current_user_claims = {}
            else:
                # Required authentication
                try:
                    from flask_jwt_extended import verify_jwt_in_request
                    verify_jwt_in_request()
                    
                    user_id = get_jwt_identity()
                    if not user_id:
                        return jsonify({
                            'error': 'invalid_token',
                            'message': 'Invalid user identity in token'
                        }), 401
                    
                    # Check if user tokens are revoked
                    from .jwt_manager import jwt_manager
                    if jwt_manager.is_user_tokens_revoked(user_id):
                        return jsonify({
                            'error': 'token_revoked',
                            'message': 'User tokens have been revoked'
                        }), 401
                    
                    # Load user to ensure they still exist and are active
                    from ..models.user import User
                    user = User.query.get(user_id)
                    if not user or not user.active:
                        return jsonify({
                            'error': 'user_inactive',
                            'message': 'User account is inactive'
                        }), 401
                    
                    # Check if account is locked
                    if user.is_locked:
                        return jsonify({
                            'error': 'account_locked',
                            'message': 'Account is temporarily locked'
                        }), 423
                    
                    g.current_user = user
                    g.current_user_id = user_id
                    g.current_user_claims = get_jwt()
                    
                except Exception as e:
                    return jsonify({
                        'error': 'authentication_failed',
                        'message': 'Authentication failed'
                    }), 401
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Admin role required decorator
    """
    @wraps(f)
    @auth_required()
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'current_user', None)
        if not user or not user.is_admin:
            return jsonify({
                'error': 'insufficient_privileges',
                'message': 'Admin privileges required'
            }), 403
        
        # Log admin action
        from ..models.audit import AuditLog, EventType
        AuditLog.log_event(
            EventType.ADMIN_ACTION,
            user=user,
            request=request,
            message=f"Admin accessed {request.endpoint}"
        )
        
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_roles: List[str]):
    """
    Role-based access control decorator
    
    Args:
        required_roles: List of role names that are allowed
    """
    def decorator(f):
        @wraps(f)
        @auth_required()
        def decorated_function(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if not user:
                return jsonify({
                    'error': 'authentication_required',
                    'message': 'Authentication required'
                }), 401
            
            # Admin bypass
            if user.is_admin:
                return f(*args, **kwargs)
            
            # Check user roles
            user_roles = [role.name for role in user.roles]
            if not any(role in user_roles for role in required_roles):
                return jsonify({
                    'error': 'insufficient_privileges',
                    'message': f'Required roles: {", ".join(required_roles)}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(limit: str, per_method: bool = False, key_func: Optional[Callable] = None):
    """
    Rate limiting decorator
    
    Args:
        limit: Rate limit string (e.g., "10 per minute")
        per_method: If True, limit per HTTP method
        key_func: Custom function to generate rate limit key
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Custom rate limiting logic
            if not hasattr(current_app, '_rate_limiter'):
                # Initialize simple in-memory rate limiter
                current_app._rate_limiter = {}
            
            # Generate rate limit key
            if key_func:
                key = key_func()
            else:
                key = get_remote_address()
                if per_method:
                    key = f"{key}:{request.method}"
                key = f"{key}:{request.endpoint}"
            
            # Parse limit (simplified parser)
            try:
                parts = limit.split(' per ')
                count = int(parts[0])
                period = parts[1]
                
                period_seconds = {
                    'second': 1,
                    'minute': 60,
                    'hour': 3600,
                    'day': 86400
                }.get(period, 60)
                
                current_time = time.time()
                window_start = current_time - period_seconds
                
                # Clean old entries
                if key in current_app._rate_limiter:
                    current_app._rate_limiter[key] = [
                        timestamp for timestamp in current_app._rate_limiter[key]
                        if timestamp > window_start
                    ]
                else:
                    current_app._rate_limiter[key] = []
                
                # Check rate limit
                if len(current_app._rate_limiter[key]) >= count:
                    # Log rate limit exceeded
                    from ..models.audit import AuditLog, EventType
                    AuditLog.log_event(
                        EventType.RATE_LIMIT_EXCEEDED,
                        ip_address=get_remote_address(),
                        request=request,
                        message=f"Rate limit exceeded: {limit}"
                    )
                    
                    return jsonify({
                        'error': 'rate_limit_exceeded',
                        'message': f'Rate limit exceeded: {limit}'
                    }), 429
                
                # Add current request
                current_app._rate_limiter[key].append(current_time)
                
            except Exception:
                # If rate limiting fails, allow the request
                pass
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_json(required_fields: List[str] = None, optional_fields: List[str] = None):
    """
    JSON validation decorator
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names (for documentation)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': 'invalid_content_type',
                    'message': 'Content-Type must be application/json'
                }), 400
            
            data = request.get_json()
            if data is None:
                return jsonify({
                    'error': 'invalid_json',
                    'message': 'Invalid JSON data'
                }), 400
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'missing_fields',
                        'message': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
            
            # Sanitize input data
            from .security import security_manager
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    sanitized_data[key] = security_manager.sanitize_input(value)
                else:
                    sanitized_data[key] = value
            
            # Store sanitized data in request context
            g.json_data = sanitized_data
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_user_ownership(resource_param: str = 'session_id', 
                          resource_model = None,
                          user_field: str = 'user_id'):
    """
    Validate that the current user owns the requested resource
    
    Args:
        resource_param: Parameter name that contains the resource ID
        resource_model: SQLAlchemy model class
        user_field: Field name in the model that contains the user ID
    """
    def decorator(f):
        @wraps(f)
        @auth_required()
        def decorated_function(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if not user:
                return jsonify({
                    'error': 'authentication_required',
                    'message': 'Authentication required'
                }), 401
            
            # Admin bypass
            if user.is_admin:
                return f(*args, **kwargs)
            
            # Get resource ID from URL parameters or JSON data
            resource_id = kwargs.get(resource_param) or \
                         request.view_args.get(resource_param) or \
                         getattr(g, 'json_data', {}).get(resource_param)
            
            if not resource_id:
                return jsonify({
                    'error': 'missing_parameter',
                    'message': f'Missing parameter: {resource_param}'
                }), 400
            
            # Check resource ownership
            if resource_model:
                resource = resource_model.query.get(resource_id)
                if not resource:
                    return jsonify({
                        'error': 'resource_not_found',
                        'message': 'Resource not found'
                    }), 404
                
                if getattr(resource, user_field) != user.id:
                    return jsonify({
                        'error': 'access_denied',
                        'message': 'Access denied to this resource'
                    }), 403
                
                # Store resource in context for use in the view
                g.resource = resource
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_api_call(log_request_body: bool = False, log_response_body: bool = False):
    """
    Log API calls for audit purposes
    
    Args:
        log_request_body: Whether to log request body
        log_response_body: Whether to log response body
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            # Execute the function
            response = f(*args, **kwargs)
            
            # Calculate response time
            response_time = int((time.time() - start_time) * 1000)
            
            # Log the API call
            from ..models.audit import AuditLog, EventType
            user = getattr(g, 'current_user', None)
            
            metadata = {
                'endpoint': request.endpoint,
                'response_time_ms': response_time
            }
            
            if log_request_body and request.is_json:
                metadata['request_body'] = request.get_json()
            
            if log_response_body and hasattr(response, 'get_json'):
                try:
                    metadata['response_body'] = response.get_json()
                except Exception:
                    pass
            
            AuditLog.log_event(
                EventType.API_CALL,
                user=user,
                request=request,
                response_status=response.status_code if hasattr(response, 'status_code') else 200,
                response_time_ms=response_time,
                metadata=metadata
            )
            
            return response
        return decorated_function
    return decorator
