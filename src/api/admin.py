"""
Admin API endpoints for system management
"""
from flask import Blueprint, request, jsonify, g
import logging

from ..auth.decorators import admin_required, validate_json, rate_limit, log_api_call
from ..services.user_service import user_service
from ..services.docker_service import docker_service
from ..models.user import User, Role, db
from ..models.session import BrowserSession, SessionStatus
from ..models.audit import AuditLog
from ..utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create admin blueprint
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@admin_required
@log_api_call()
def list_users():
    """List all users with pagination and search"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        search = request.args.get('search', '').strip()
        
        # Get users with pagination
        result = user_service.list_all_users(page, per_page, search)
        
        return success_response(
            'Users retrieved successfully',
            result
        )
        
    except Exception as e:
        logger.error(f"Admin users listing error: {e}")
        return error_response(
            'users_retrieval_failed',
            'Failed to retrieve users'
        ), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
@log_api_call()
def get_user(user_id):
    """Get detailed information about a specific user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Get user statistics
        statistics = user_service.get_user_statistics(user)
        
        # Get user sessions
        sessions = user_service.get_user_sessions(user)
        
        return success_response(
            'User details retrieved successfully',
            {
                'user': user.to_dict(),
                'statistics': statistics,
                'sessions': sessions[:10]  # Latest 10 sessions
            }
        )
        
    except Exception as e:
        logger.error(f"Admin user retrieval error: {e}")
        return error_response(
            'user_retrieval_failed',
            'Failed to retrieve user details'
        ), 500

@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@admin_required
@log_api_call()
def activate_user(user_id):
    """Activate a user account"""
    try:
        user = User.query.get_or_404(user_id)
        admin = g.current_user
        
        if user.active:
            return error_response(
                'user_already_active',
                'User account is already active'
            ), 400
        
        user.active = True
        user.locked_until = None
        user.failed_login_attempts = 0
        db.session.commit()
        
        # Log admin action
        AuditLog.log_event(
            AuditLog.EventType.USER_ACTIVATED,
            user=admin,
            resource_type='user',
            resource_id=str(user_id),
            message=f"User {user.username} activated by admin {admin.username}"
        )
        
        logger.info(f"Admin {admin.username} activated user {user.username}")
        
        return success_response(
            'User activated successfully',
            {'user': user.to_dict()}
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"User activation error: {e}")
        return error_response(
            'activation_failed',
            'Failed to activate user'
        ), 500

@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@admin_required
@log_api_call()
def deactivate_user(user_id):
    """Deactivate a user account"""
    try:
        user = User.query.get_or_404(user_id)
        admin = g.current_user
        
        # Prevent self-deactivation
        if user.id == admin.id:
            return error_response(
                'cannot_deactivate_self',
                'Cannot deactivate your own account'
            ), 400
        
        if not user.active:
            return error_response(
                'user_already_inactive',
                'User account is already inactive'
            ), 400
        
        user.active = False
        db.session.commit()
        
        # Stop all user sessions
        active_sessions = user.browser_sessions.filter_by(status=SessionStatus.RUNNING).all()
        for session in active_sessions:
            if session.container_id:
                docker_service.stop_container(session.container_id)
            session.update_status(SessionStatus.STOPPED, "Account deactivated")
        
        # Revoke all user tokens
        from ..auth.jwt_manager import jwt_manager
        jwt_manager.revoke_user_tokens(user.id)
        
        # Log admin action
        AuditLog.log_event(
            AuditLog.EventType.USER_DEACTIVATED,
            user=admin,
            resource_type='user',
            resource_id=str(user_id),
            message=f"User {user.username} deactivated by admin {admin.username}"
        )
        
        logger.info(f"Admin {admin.username} deactivated user {user.username}")
        
        return success_response(
            'User deactivated successfully',
            {'user': user.to_dict()}
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"User deactivation error: {e}")
        return error_response(
            'deactivation_failed',
            'Failed to deactivate user'
        ), 500

@admin_bp.route('/users/<int:user_id>/unlock', methods=['POST'])
@admin_required
@log_api_call()
def unlock_user(user_id):
    """Unlock a locked user account"""
    try:
        user = User.query.get_or_404(user_id)
        admin = g.current_user
        
        if not user.is_locked:
            return error_response(
                'user_not_locked',
                'User account is not locked'
            ), 400
        
        user.unlock_account()
        
        # Log admin action
        AuditLog.log_event(
            AuditLog.EventType.ACCOUNT_UNLOCKED,
            user=admin,
            resource_type='user',
            resource_id=str(user_id),
            message=f"User {user.username} unlocked by admin {admin.username}"
        )
        
        logger.info(f"Admin {admin.username} unlocked user {user.username}")
        
        return success_response(
            'User account unlocked successfully',
            {'user': user.to_dict()}
        )
        
    except Exception as e:
        logger.error(f"User unlock error: {e}")
        return error_response(
            'unlock_failed',
            'Failed to unlock user account'
        ), 500

@admin_bp.route('/sessions', methods=['GET'])
@admin_required
@log_api_call()
def list_all_sessions():
    """List all browser sessions across all users"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        status = request.args.get('status')
        user_id = request.args.get('user_id')
        
        # Build query
        query = BrowserSession.query
        
        if status and status in [s.value for s in SessionStatus]:
            query = query.filter_by(status=SessionStatus(status))
        
        if user_id:
            query = query.filter_by(user_id=int(user_id))
        
        # Paginate results
        pagination = query.order_by(BrowserSession.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        sessions = []
        for session in pagination.items:
            session_data = session.to_dict()
            session_data['user'] = {
                'id': session.user.id,
                'username': session.user.username,
                'email': session.user.email
            }
            
            # Get container status for active sessions
            if session.is_active and session.container_id:
                container_status = docker_service.get_container_status(session.container_id)
                session_data['container_status'] = container_status
            
            sessions.append(session_data)
        
        return success_response(
            'Sessions retrieved successfully',
            {
                'sessions': sessions,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Admin sessions listing error: {e}")
        return error_response(
            'sessions_retrieval_failed',
            'Failed to retrieve sessions'
        ), 500

@admin_bp.route('/sessions/<session_id>/stop', methods=['POST'])
@admin_required
@log_api_call()
def stop_any_session(session_id):
    """Stop any user's browser session (admin override)"""
    try:
        session = BrowserSession.query.get_or_404(session_id)
        admin = g.current_user
        
        if session.status not in [SessionStatus.RUNNING, SessionStatus.CREATING]:
            return error_response(
                'session_not_running',
                'Session is not currently running'
            ), 400
        
        # Stop Docker container
        if session.container_id:
            success = docker_service.stop_container(session.container_id)
            if not success:
                logger.warning(f"Failed to stop container {session.container_id}")
        
        # Update session status
        session.update_status(SessionStatus.STOPPED, "Stopped by admin")
        
        # Log admin action
        AuditLog.log_event(
            'admin_session_stop',
            user=admin,
            resource_type='session',
            resource_id=session_id,
            message=f"Session stopped by admin {admin.username} (owner: {session.user.username})"
        )
        
        logger.info(f"Admin {admin.username} stopped session {session_id}")
        
        return success_response(
            'Session stopped successfully',
            {'session': session.to_dict()}
        )
        
    except Exception as e:
        logger.error(f"Admin session stop error: {e}")
        return error_response(
            'session_stop_failed',
            'Failed to stop session'
        ), 500

@admin_bp.route('/system/stats', methods=['GET'])
@admin_required
@log_api_call()
def get_system_stats():
    """Get system statistics and resource usage"""
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(active=True).count()
        users_last_24h = User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        # Session statistics
        total_sessions = BrowserSession.query.count()
        active_sessions = BrowserSession.query.filter_by(status=SessionStatus.RUNNING).count()
        sessions_last_24h = BrowserSession.query.filter(
            BrowserSession.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        # Browser usage statistics
        browser_usage = db.session.query(
            BrowserSession.browser_type,
            func.count(BrowserSession.id).label('count')
        ).group_by(BrowserSession.browser_type).all()
        
        # Docker system resources
        docker_resources = docker_service.get_system_resources()
        
        # Recent audit events
        recent_events = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
        
        return success_response(
            'System statistics retrieved successfully',
            {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'new_last_24h': users_last_24h
                },
                'sessions': {
                    'total': total_sessions,
                    'active': active_sessions,
                    'new_last_24h': sessions_last_24h
                },
                'browser_usage': {
                    usage.browser_type.value: usage.count 
                    for usage in browser_usage
                },
                'docker_resources': docker_resources,
                'recent_events': [event.to_dict() for event in recent_events]
            }
        )
        
    except Exception as e:
        logger.error(f"System stats error: {e}")
        return error_response(
            'stats_retrieval_failed',
            'Failed to retrieve system statistics'
        ), 500

@admin_bp.route('/system/cleanup', methods=['POST'])
@admin_required
@rate_limit("1 per hour")
@log_api_call()
def system_cleanup():
    """Perform system cleanup tasks"""
    try:
        admin = g.current_user
        cleanup_results = {}
        
        # Clean up expired containers
        cleaned_containers = docker_service.cleanup_expired_containers()
        cleanup_results['expired_containers'] = cleaned_containers
        
        # Clean up expired sessions
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        expired_sessions = BrowserSession.query.filter(
            BrowserSession.expires_at < datetime.utcnow(),
            BrowserSession.status.in_([SessionStatus.RUNNING, SessionStatus.CREATING])
        ).all()
        
        cleaned_sessions = 0
        for session in expired_sessions:
            try:
                if session.container_id:
                    docker_service.stop_container(session.container_id)
                    docker_service.remove_container(session.container_id, force=True)
                
                session.update_status(SessionStatus.EXPIRED)
                cleaned_sessions += 1
                
            except Exception as e:
                logger.error(f"Error cleaning session {session.id}: {e}")
        
        cleanup_results['expired_sessions'] = cleaned_sessions
        
        # Log cleanup action
        AuditLog.log_event(
            'system_cleanup',
            user=admin,
            message=f"System cleanup performed: {cleaned_containers} containers, {cleaned_sessions} sessions",
            metadata=cleanup_results
        )
        
        logger.info(f"Admin {admin.username} performed system cleanup")
        
        return success_response(
            'System cleanup completed successfully',
            cleanup_results
        )
        
    except Exception as e:
        logger.error(f"System cleanup error: {e}")
        return error_response(
            'cleanup_failed',
            'Failed to perform system cleanup'
        ), 500

@admin_bp.route('/audit-logs', methods=['GET'])
@admin_required
@log_api_call()
def get_audit_logs():
    """Get audit logs with filtering"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 200)
        event_type = request.args.get('event_type')
        user_id = request.args.get('user_id')
        severity = request.args.get('severity')
        
        # Build query
        query = AuditLog.query
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        if user_id:
            query = query.filter_by(user_id=int(user_id))
        
        if severity:
            query = query.filter_by(severity=severity)
        
        # Paginate results
        pagination = query.order_by(AuditLog.timestamp.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        logs = []
        for log in pagination.items:
            log_data = log.to_dict()
            if log.user:
                log_data['user'] = {
                    'id': log.user.id,
                    'username': log.user.username,
                    'email': log.user.email
                }
            logs.append(log_data)
        
        return success_response(
            'Audit logs retrieved successfully',
            {
                'logs': logs,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Audit logs retrieval error: {e}")
        return error_response(
            'logs_retrieval_failed',
            'Failed to retrieve audit logs'
        ), 500

@admin_bp.route('/docker/pull-images', methods=['POST'])
@admin_required
@rate_limit("1 per hour")
@log_api_call()
def pull_docker_images():
    """Pull/update Docker browser images"""
    try:
        admin = g.current_user
        
        # Pull browser images
        results = docker_service.pull_browser_images()
        
        # Log admin action
        AuditLog.log_event(
            'docker_images_updated',
            user=admin,
            message=f"Docker images update initiated by admin {admin.username}",
            metadata={'results': results}
        )
        
        logger.info(f"Admin {admin.username} initiated Docker images update")
        
        return success_response(
            'Docker images update initiated',
            {'results': results}
        )
        
    except Exception as e:
        logger.error(f"Docker images pull error: {e}")
        return error_response(
            'images_pull_failed',
            'Failed to pull Docker images'
        ), 500

# Error handlers for admin blueprint
@admin_bp.errorhandler(403)
def admin_access_denied(error):
    return error_response(
        'admin_access_required',
        'Administrator privileges are required to access this resource'
    ), 403
