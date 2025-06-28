"""
Authentication API endpoints
"""
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import get_jwt, get_jwt_identity
import logging

from ..auth.decorators import auth_required, validate_json, rate_limit, log_api_call
from ..auth.validators import validate_registration_data, validate_login_data
from ..services.user_service import user_service
from ..utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@rate_limit("5 per minute")
@validate_json(['email', 'username', 'password', 'password_confirm'])
@log_api_call()
def register():
    """Register a new user account"""
    try:
        data = g.json_data
        
        # Validate registration data
        validation_result = validate_registration_data(data)
        if not validation_result['valid']:
            return error_response(
                'validation_failed',
                'Registration data validation failed',
                validation_result['errors']
            ), 400
        
        # Create user account
        result = user_service.create_user(validation_result['data'])
        
        if result['success']:
            return success_response(
                'User account created successfully',
                {
                    'user': result['user'],
                    'message': result['message']
                }
            ), 201
        else:
            return error_response(
                result['error'],
                result['message']
            ), 400
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return error_response(
            'registration_failed',
            'Registration service error'
        ), 500

@auth_bp.route('/login', methods=['POST'])
@rate_limit("10 per minute")
@validate_json(['password'])
@log_api_call()
def login():
    """Authenticate user and return JWT tokens"""
    try:
        data = g.json_data
        
        # Validate login data
        validation_result = validate_login_data(data)
        if not validation_result['valid']:
            return error_response(
                'validation_failed',
                'Login data validation failed',
                validation_result['errors']
            ), 400
        
        # Get client IP for audit logging
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Authenticate user
        result = user_service.authenticate_user(
            validation_result['data']['identifier'],
            validation_result['data']['password'],
            client_ip
        )
        
        if result['success']:
            return success_response(
                'Login successful',
                {
                    'user': result['user'],
                    'access_token': result['tokens']['access_token'],
                    'refresh_token': result['tokens']['refresh_token'],
                    'expires_in': result['tokens']['expires_in']
                }
            )
        else:
            return error_response(
                result['error'],
                result['message']
            ), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return error_response(
            'login_failed',
            'Authentication service error'
        ), 500

@auth_bp.route('/logout', methods=['POST'])
@auth_required()
@log_api_call()
def logout():
    """Logout user and blacklist token"""
    try:
        user = g.current_user
        token_jti = get_jwt().get('jti')
        
        # Logout user
        result = user_service.logout_user(user, token_jti)
        
        if result['success']:
            return success_response(result['message'])
        else:
            return error_response(
                result['error'],
                result['message']
            ), 500
            
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return error_response(
            'logout_failed',
            'Logout service error'
        ), 500

@auth_bp.route('/refresh', methods=['POST'])
@auth_required()
@log_api_call()
def refresh():
    """Refresh access token using refresh token"""
    try:
        from ..auth.jwt_manager import jwt_manager
        
        user = g.current_user
        
        # Create new access token
        token_result = jwt_manager.refresh_access_token(user)
        
        return success_response(
            'Token refreshed successfully',
            {
                'access_token': token_result['access_token'],
                'expires_in': token_result['expires_in']
            }
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return error_response(
            'refresh_failed',
            'Token refresh service error'
        ), 500

@auth_bp.route('/profile', methods=['GET'])
@auth_required()
@log_api_call()
def get_profile():
    """Get current user profile"""
    try:
        user = g.current_user
        
        # Get user statistics
        statistics = user_service.get_user_statistics(user)
        
        return success_response(
            'Profile retrieved successfully',
            {
                'user': user.to_dict(),
                'statistics': statistics
            }
        )
        
    except Exception as e:
        logger.error(f"Profile retrieval error: {e}")
        return error_response(
            'profile_retrieval_failed',
            'Profile service error'
        ), 500

@auth_bp.route('/profile', methods=['PUT'])
@auth_required()
@validate_json()
@log_api_call()
def update_profile():
    """Update user profile"""
    try:
        user = g.current_user
        data = g.json_data
        
        # Update user profile
        result = user_service.update_user_profile(user, data)
        
        if result['success']:
            return success_response(
                result['message'],
                {
                    'user': result['user'],
                    'updated_fields': result['updated_fields']
                }
            )
        else:
            return error_response(
                result['error'],
                result['message']
            ), 400
            
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return error_response(
            'profile_update_failed',
            'Profile update service error'
        ), 500

@auth_bp.route('/change-password', methods=['POST'])
@auth_required()
@rate_limit("3 per hour")
@validate_json(['current_password', 'new_password'])
@log_api_call()
def change_password():
    """Change user password"""
    try:
        from ..auth.validators import validate_password
        
        user = g.current_user
        data = g.json_data
        
        # Validate new password
        password_validation = validate_password(
            data['new_password'],
            username=user.username,
            email=user.email
        )
        
        if not password_validation['valid']:
            return error_response(
                'validation_failed',
                'New password validation failed',
                {'new_password': password_validation['errors']}
            ), 400
        
        # Change password
        result = user_service.change_password(
            user,
            data['current_password'],
            data['new_password']
        )
        
        if result['success']:
            return success_response(result['message'])
        else:
            return error_response(
                result['error'],
                result['message']
            ), 400
            
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return error_response(
            'password_change_failed',
            'Password change service error'
        ), 500

@auth_bp.route('/2fa/setup', methods=['POST'])
@auth_required()
@rate_limit("3 per hour")
@log_api_call()
def setup_2fa():
    """Set up two-factor authentication"""
    try:
        user = g.current_user
        
        # Set up 2FA
        result = user_service.setup_two_factor_auth(user)
        
        if result['success']:
            return success_response(
                result['message'],
                {
                    'qr_code': result['qr_code'],
                    'secret': result['secret']
                }
            )
        else:
            return error_response(
                result['error'],
                result['message']
            ), 500
            
    except Exception as e:
        logger.error(f"2FA setup error: {e}")
        return error_response(
            'setup_failed',
            '2FA setup service error'
        ), 500

@auth_bp.route('/2fa/verify', methods=['POST'])
@auth_required()
@rate_limit("10 per hour")
@validate_json(['token'])
@log_api_call()
def verify_2fa():
    """Verify two-factor authentication token"""
    try:
        user = g.current_user
        data = g.json_data
        
        # Verify 2FA token
        result = user_service.verify_two_factor_auth(user, data['token'])
        
        if result['success']:
            return success_response(result['message'])
        else:
            return error_response(
                result['error'],
                result['message']
            ), 400
            
    except Exception as e:
        logger.error(f"2FA verification error: {e}")
        return error_response(
            'verification_failed',
            '2FA verification service error'
        ), 500

@auth_bp.route('/sessions', methods=['GET'])
@auth_required()
@log_api_call()
def get_user_sessions():
    """Get all browser sessions for current user"""
    try:
        user = g.current_user
        
        # Get user sessions
        sessions = user_service.get_user_sessions(user)
        
        return success_response(
            'Sessions retrieved successfully',
            {'sessions': sessions}
        )
        
    except Exception as e:
        logger.error(f"Sessions retrieval error: {e}")
        return error_response(
            'sessions_retrieval_failed',
            'Sessions service error'
        ), 500

@auth_bp.route('/validate', methods=['GET'])
@auth_required()
def validate_token():
    """Validate current JWT token"""
    try:
        user = g.current_user
        claims = g.current_user_claims
        
        return success_response(
            'Token is valid',
            {
                'user': user.to_dict(),
                'token_info': {
                    'issued_at': claims.get('iat'),
                    'expires_at': claims.get('exp'),
                    'roles': claims.get('roles', []),
                    'is_admin': claims.get('is_admin', False)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return error_response(
            'validation_failed',
            'Token validation service error'
        ), 500

# Error handlers for authentication blueprint
@auth_bp.errorhandler(400)
def bad_request(error):
    return error_response(
        'bad_request',
        'The request could not be understood by the server'
    ), 400

@auth_bp.errorhandler(401)
def unauthorized(error):
    return error_response(
        'unauthorized',
        'Authentication credentials were not provided or are invalid'
    ), 401

@auth_bp.errorhandler(403)
def forbidden(error):
    return error_response(
        'forbidden',
        'You do not have permission to access this resource'
    ), 403

@auth_bp.errorhandler(422)
def unprocessable_entity(error):
    return error_response(
        'unprocessable_entity',
        'The request was well-formed but contains invalid data'
    ), 422

@auth_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return error_response(
        'rate_limit_exceeded',
        'Too many requests. Please try again later.'
    ), 429

@auth_bp.errorhandler(500)
def internal_server_error(error):
    return error_response(
        'internal_server_error',
        'An internal server error occurred'
    ), 500
