"""
User service for managing user accounts and operations
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import current_app, request
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service for user management operations"""
    
    def __init__(self):
        pass
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user account
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            Result dictionary with user info or error
        """
        from ..models.user import User, Role, db
        from ..models.audit import AuditLog, EventType
        from ..auth.security import security_manager
        
        try:
            # Check if user already exists
            existing_user = User.query.filter(
                (User.email == user_data['email']) | 
                (User.username == user_data['username'])
            ).first()
            
            if existing_user:
                if existing_user.email == user_data['email']:
                    return {
                        'success': False,
                        'error': 'email_exists',
                        'message': 'Email address is already registered'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'username_exists',
                        'message': 'Username is already taken'
                    }
            
            # Hash password
            hashed_password = security_manager.hash_password(user_data['password'])
            
            # Create user
            user = User(
                email=user_data['email'],
                username=user_data['username'],
                password=hashed_password,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                active=True,
                confirmed_at=datetime.utcnow()  # Auto-confirm for now
            )
            
            # Assign default user role
            user_role = Role.query.filter_by(name='user').first()
            if user_role:
                user.roles.append(user_role)
            
            db.session.add(user)
            db.session.commit()
            
            # Log user creation
            AuditLog.log_event(
                EventType.USER_CREATED,
                user=user,
                request=request,
                message=f"User account created: {user.username}"
            )
            
            logger.info(f"Created user account: {user.username}")
            
            return {
                'success': True,
                'user': user.to_dict(),
                'message': 'User account created successfully'
            }
            
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Integrity error creating user: {e}")
            return {
                'success': False,
                'error': 'database_error',
                'message': 'Failed to create user due to database constraint'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {e}")
            return {
                'success': False,
                'error': 'creation_failed',
                'message': 'Failed to create user account'
            }
    
    def authenticate_user(self, identifier: str, password: str, 
                         ip_address: str = None) -> Dict[str, Any]:
        """
        Authenticate user with email/username and password
        
        Args:
            identifier: Email or username
            password: User password
            ip_address: Client IP address
            
        Returns:
            Authentication result dictionary
        """
        from ..models.user import User, db
        from ..models.audit import AuditLog, EventType
        from ..auth.security import security_manager
        from ..auth.jwt_manager import jwt_manager
        
        try:
            # Find user by email or username
            user = User.query.filter(
                (User.email == identifier) | (User.username == identifier)
            ).first()
            
            if not user:
                # Log failed attempt
                AuditLog.log_login_failed(
                    username=identifier,
                    ip_address=ip_address,
                    reason="User not found",
                    request=request
                )
                return {
                    'success': False,
                    'error': 'invalid_credentials',
                    'message': 'Invalid email/username or password'
                }
            
            # Check if account is locked
            if user.is_locked:
                AuditLog.log_login_failed(
                    username=user.username,
                    ip_address=ip_address,
                    reason="Account locked",
                    request=request
                )
                return {
                    'success': False,
                    'error': 'account_locked',
                    'message': 'Account is temporarily locked due to failed login attempts'
                }
            
            # Check if account is active
            if not user.active:
                AuditLog.log_login_failed(
                    username=user.username,
                    ip_address=ip_address,
                    reason="Account inactive",
                    request=request
                )
                return {
                    'success': False,
                    'error': 'account_inactive',
                    'message': 'Account is deactivated'
                }
            
            # Verify password
            if not security_manager.verify_password(password, user.password):
                user.increment_failed_login()
                
                AuditLog.log_login_failed(
                    username=user.username,
                    ip_address=ip_address,
                    reason="Invalid password",
                    request=request
                )
                return {
                    'success': False,
                    'error': 'invalid_credentials',
                    'message': 'Invalid email/username or password'
                }
            
            # Successful authentication
            user.reset_failed_login()
            
            # Update login information
            user.last_login_at = user.current_login_at
            user.last_login_ip = user.current_login_ip
            user.current_login_at = datetime.utcnow()
            user.current_login_ip = ip_address
            user.login_count += 1
            
            db.session.commit()
            
            # Create JWT tokens
            tokens = jwt_manager.create_tokens(user)
            
            # Log successful login
            AuditLog.log_login_success(user, request=request)
            
            logger.info(f"User {user.username} logged in successfully")
            
            return {
                'success': True,
                'user': user.to_dict(),
                'tokens': tokens,
                'message': 'Login successful'
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {
                'success': False,
                'error': 'authentication_failed',
                'message': 'Authentication service error'
            }
    
    def logout_user(self, user: 'User', token_jti: str = None) -> Dict[str, Any]:
        """
        Logout user and blacklist token
        
        Args:
            user: User object
            token_jti: JWT token ID to blacklist
            
        Returns:
            Logout result dictionary
        """
        from ..models.audit import AuditLog, EventType
        from ..auth.jwt_manager import jwt_manager
        
        try:
            # Blacklist token if provided
            if token_jti:
                jwt_manager.blacklist_token(token_jti)
            
            # Log logout
            AuditLog.log_event(
                EventType.LOGOUT,
                user=user,
                request=request,
                message=f"User {user.username} logged out"
            )
            
            logger.info(f"User {user.username} logged out")
            
            return {
                'success': True,
                'message': 'Logout successful'
            }
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return {
                'success': False,
                'error': 'logout_failed',
                'message': 'Logout service error'
            }
    
    def update_user_profile(self, user: 'User', update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile information
        
        Args:
            user: User object to update
            update_data: Dictionary containing update data
            
        Returns:
            Update result dictionary
        """
        from ..models.user import db
        from ..models.audit import AuditLog, EventType
        
        try:
            # Store old values for audit
            old_values = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'timezone': user.timezone,
                'preferred_browser': user.preferred_browser,
                'max_containers': user.max_containers,
                'container_timeout': user.container_timeout
            }
            
            # Update allowed fields
            updatable_fields = [
                'first_name', 'last_name', 'timezone', 'preferred_browser',
                'max_containers', 'container_timeout', 'avatar_url'
            ]
            
            updated_fields = []
            for field in updatable_fields:
                if field in update_data:
                    old_value = getattr(user, field)
                    new_value = update_data[field]
                    
                    if old_value != new_value:
                        setattr(user, field, new_value)
                        updated_fields.append(field)
            
            if updated_fields:
                user.updated_at = datetime.utcnow()
                db.session.commit()
                
                # Log profile update
                AuditLog.log_event(
                    EventType.USER_UPDATED,
                    user=user,
                    request=request,
                    message=f"User profile updated: {', '.join(updated_fields)}",
                    old_values=old_values,
                    new_values={field: getattr(user, field) for field in updated_fields}
                )
                
                logger.info(f"Updated profile for user {user.username}: {', '.join(updated_fields)}")
            
            return {
                'success': True,
                'user': user.to_dict(),
                'updated_fields': updated_fields,
                'message': 'Profile updated successfully' if updated_fields else 'No changes made'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Profile update error: {e}")
            return {
                'success': False,
                'error': 'update_failed',
                'message': 'Failed to update profile'
            }
    
    def change_password(self, user: 'User', current_password: str, 
                       new_password: str) -> Dict[str, Any]:
        """
        Change user password
        
        Args:
            user: User object
            current_password: Current password
            new_password: New password
            
        Returns:
            Password change result dictionary
        """
        from ..models.user import db
        from ..models.audit import AuditLog, EventType
        from ..auth.security import security_manager
        from ..auth.jwt_manager import jwt_manager
        
        try:
            # Verify current password
            if not security_manager.verify_password(current_password, user.password):
                return {
                    'success': False,
                    'error': 'invalid_current_password',
                    'message': 'Current password is incorrect'
                }
            
            # Hash new password
            new_hashed_password = security_manager.hash_password(new_password)
            
            # Update password
            user.password = new_hashed_password
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Revoke all existing tokens to force re-login
            jwt_manager.revoke_user_tokens(user.id)
            
            # Log password change
            AuditLog.log_event(
                EventType.PASSWORD_CHANGE,
                user=user,
                request=request,
                message=f"Password changed for user {user.username}"
            )
            
            logger.info(f"Password changed for user {user.username}")
            
            return {
                'success': True,
                'message': 'Password changed successfully. Please log in again.'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Password change error: {e}")
            return {
                'success': False,
                'error': 'password_change_failed',
                'message': 'Failed to change password'
            }
    
    def setup_two_factor_auth(self, user: 'User') -> Dict[str, Any]:
        """
        Set up two-factor authentication for user
        
        Args:
            user: User object
            
        Returns:
            2FA setup result dictionary
        """
        from ..models.user import db
        from ..models.audit import AuditLog, EventType
        from ..auth.security import security_manager
        
        try:
            # Generate TOTP secret
            totp_secret = security_manager.generate_totp_secret()
            
            # Generate QR code
            qr_code_data = security_manager.generate_totp_qr_code(totp_secret, user.email)
            
            # Store secret (encrypted)
            user.tf_totp_secret = security_manager.encrypt_data(totp_secret)
            user.tf_primary_method = 'authenticator'
            user.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log 2FA setup
            AuditLog.log_event(
                EventType.USER_UPDATED,
                user=user,
                request=request,
                message=f"Two-factor authentication setup initiated for {user.username}"
            )
            
            logger.info(f"2FA setup initiated for user {user.username}")
            
            return {
                'success': True,
                'qr_code': qr_code_data,
                'secret': totp_secret,  # Return for manual entry
                'message': 'Scan the QR code with your authenticator app'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"2FA setup error: {e}")
            return {
                'success': False,
                'error': 'setup_failed',
                'message': 'Failed to set up two-factor authentication'
            }
    
    def verify_two_factor_auth(self, user: 'User', token: str) -> Dict[str, Any]:
        """
        Verify two-factor authentication token
        
        Args:
            user: User object
            token: TOTP token to verify
            
        Returns:
            Verification result dictionary
        """
        from ..auth.security import security_manager
        
        try:
            if not user.tf_totp_secret:
                return {
                    'success': False,
                    'error': 'no_2fa_setup',
                    'message': 'Two-factor authentication is not set up'
                }
            
            # Decrypt secret
            decrypted_secret = security_manager.decrypt_data(user.tf_totp_secret)
            
            # Verify token
            is_valid = security_manager.verify_totp_token(decrypted_secret, token)
            
            if is_valid:
                logger.info(f"2FA token verified for user {user.username}")
                return {
                    'success': True,
                    'message': 'Two-factor authentication verified'
                }
            else:
                logger.warning(f"Invalid 2FA token for user {user.username}")
                return {
                    'success': False,
                    'error': 'invalid_token',
                    'message': 'Invalid authentication token'
                }
                
        except Exception as e:
            logger.error(f"2FA verification error: {e}")
            return {
                'success': False,
                'error': 'verification_failed',
                'message': 'Failed to verify two-factor authentication'
            }
    
    def get_user_sessions(self, user: 'User') -> List[Dict[str, Any]]:
        """
        Get all browser sessions for a user
        
        Args:
            user: User object
            
        Returns:
            List of session dictionaries
        """
        try:
            sessions = user.browser_sessions.order_by('created_at desc').all()
            return [session.to_dict() for session in sessions]
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    def get_user_statistics(self, user: 'User') -> Dict[str, Any]:
        """
        Get user statistics and usage information
        
        Args:
            user: User object
            
        Returns:
            Statistics dictionary
        """
        try:
            from ..models.session import BrowserSession, SessionStatus
            from sqlalchemy import func
            
            # Get session statistics
            total_sessions = user.browser_sessions.count()
            active_sessions = user.browser_sessions.filter_by(status=SessionStatus.RUNNING).count()
            
            # Get total session time
            completed_sessions = user.browser_sessions.filter(
                BrowserSession.session_duration.isnot(None)
            ).all()
            
            total_session_time = sum(session.session_duration for session in completed_sessions)
            
            # Get most used browser
            browser_usage = user.browser_sessions.with_entities(
                BrowserSession.browser_type,
                func.count(BrowserSession.id).label('count')
            ).group_by(BrowserSession.browser_type).all()
            
            most_used_browser = max(browser_usage, key=lambda x: x.count)[0].value if browser_usage else None
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'total_session_time_seconds': total_session_time,
                'total_session_time_hours': round(total_session_time / 3600, 2),
                'most_used_browser': most_used_browser,
                'browser_usage': {usage.browser_type.value: usage.count for usage in browser_usage},
                'account_created': user.created_at.isoformat(),
                'last_login': user.last_login_at.isoformat() if user.last_login_at else None,
                'login_count': user.login_count
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {}
    
    def list_all_users(self, page: int = 1, per_page: int = 20, 
                      search: str = None) -> Dict[str, Any]:
        """
        List all users (admin function)
        
        Args:
            page: Page number
            per_page: Users per page
            search: Search term for username/email
            
        Returns:
            Paginated users dictionary
        """
        from ..models.user import User
        
        try:
            query = User.query
            
            # Apply search filter
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (User.username.ilike(search_term)) |
                    (User.email.ilike(search_term)) |
                    (User.first_name.ilike(search_term)) |
                    (User.last_name.ilike(search_term))
                )
            
            # Paginate results
            pagination = query.order_by(User.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'users': [user.to_dict() for user in pagination.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return {
                'users': [],
                'pagination': {
                    'page': 1,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0,
                    'has_prev': False,
                    'has_next': False
                }
            }

# Global user service instance
user_service = UserService()
