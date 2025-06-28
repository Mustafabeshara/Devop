"""
Browser sessions API endpoints
"""
from flask import Blueprint, request, jsonify, g
import logging

from ..auth.decorators import auth_required, validate_json, rate_limit, log_api_call, validate_user_ownership
from ..auth.validators import validate_session_data
from ..models.session import BrowserSession, SessionStatus, BrowserType
from ..models.user import db
from ..services.docker_service import docker_service
from ..utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create sessions blueprint
sessions_bp = Blueprint('sessions', __name__)

@sessions_bp.route('/', methods=['GET'])
@auth_required()
@log_api_call()
def list_sessions():
    """List all browser sessions for current user"""
    try:
        user = g.current_user
        
        # Get query parameters
        status = request.args.get('status')
        browser_type = request.args.get('browser_type')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Build query
        query = user.browser_sessions
        
        if status and status in [s.value for s in SessionStatus]:
            query = query.filter_by(status=SessionStatus(status))
        
        if browser_type and browser_type in [b.value for b in BrowserType]:
            query = query.filter_by(browser_type=BrowserType(browser_type))
        
        # Paginate results
        pagination = query.order_by(BrowserSession.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        sessions = []
        for session in pagination.items:
            session_data = session.to_dict()
            
            # Get real-time container status if running
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
        logger.error(f"Sessions listing error: {e}")
        return error_response(
            'sessions_retrieval_failed',
            'Failed to retrieve sessions'
        ), 500

@sessions_bp.route('/', methods=['POST'])
@auth_required()
@rate_limit("10 per hour")
@validate_json()
@log_api_call()
def create_session():
    """Create a new browser session"""
    try:
        user = g.current_user
        data = g.json_data
        
        # Check if user has reached maximum containers
        active_sessions = user.browser_sessions.filter_by(status=SessionStatus.RUNNING).count()
        if active_sessions >= user.max_containers:
            return error_response(
                'max_containers_reached',
                f'Maximum number of containers ({user.max_containers}) reached'
            ), 429
        
        # Validate session data
        validation_result = validate_session_data(data)
        if not validation_result['valid']:
            return error_response(
                'validation_failed',
                'Session data validation failed',
                validation_result['errors']
            ), 400
        
        # Check Docker service availability
        if not docker_service.is_available():
            return error_response(
                'service_unavailable',
                'Container service is not available'
            ), 503
        
        # Create session record
        session_data = validation_result['data']
        session_data['user_id'] = user.id
        
        session = BrowserSession(**session_data)
        session.id = docker_service._generate_secure_session_id() if hasattr(docker_service, '_generate_secure_session_id') else session.id
        
        db.session.add(session)
        db.session.flush()  # Get session ID
        
        try:
            # Create Docker container
            container_info = docker_service.create_browser_container(session_data)
            
            # Update session with container information
            session.container_id = container_info['container_id']
            session.container_name = container_info['container_name']
            session.docker_image = container_info['docker_image']
            session.vnc_port = container_info['vnc_port']
            session.web_port = container_info['web_port']
            session.vnc_password = container_info['vnc_password']
            session.access_url = container_info['access_url']
            session.status = SessionStatus.RUNNING
            session.started_at = container_info['created_at']
            
            db.session.commit()
            
            # Log session creation
            from ..models.audit import AuditLog
            AuditLog.log_session_event(
                AuditLog.EventType.SESSION_CREATED if hasattr(AuditLog.EventType, 'SESSION_CREATED') else 'session_created',
                session,
                user=user,
                message=f"Browser session created: {session.session_name}"
            )
            
            logger.info(f"Created browser session {session.id} for user {user.username}")
            
            return success_response(
                'Session created successfully',
                {'session': session.to_dict()}
            ), 201
            
        except Exception as container_error:
            # Rollback session creation if container fails
            db.session.rollback()
            logger.error(f"Container creation failed: {container_error}")
            return error_response(
                'container_creation_failed',
                f'Failed to create browser container: {str(container_error)}'
            ), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Session creation error: {e}")
        return error_response(
            'session_creation_failed',
            'Failed to create session'
        ), 500

@sessions_bp.route('/<session_id>', methods=['GET'])
@auth_required()
@validate_user_ownership('session_id', BrowserSession)
@log_api_call()
def get_session(session_id):
    """Get details of a specific session"""
    try:
        session = g.resource  # Set by validate_user_ownership decorator
        
        session_data = session.to_dict()
        
        # Get real-time container status if running
        if session.is_active and session.container_id:
            container_status = docker_service.get_container_status(session.container_id)
            session_data['container_status'] = container_status
            
            # Update last accessed time
            session.update_last_accessed()
        
        return success_response(
            'Session retrieved successfully',
            {'session': session_data}
        )
        
    except Exception as e:
        logger.error(f"Session retrieval error: {e}")
        return error_response(
            'session_retrieval_failed',
            'Failed to retrieve session'
        ), 500

@sessions_bp.route('/<session_id>', methods=['PUT'])
@auth_required()
@validate_user_ownership('session_id', BrowserSession)
@validate_json()
@log_api_call()
def update_session(session_id):
    """Update session settings"""
    try:
        session = g.resource
        data = g.json_data
        user = g.current_user
        
        # Only allow updating certain fields
        updatable_fields = ['session_name', 'screen_resolution']
        updated_fields = []
        
        for field in updatable_fields:
            if field in data:
                old_value = getattr(session, field)
                new_value = data[field]
                
                if old_value != new_value:
                    setattr(session, field, new_value)
                    updated_fields.append(field)
        
        if updated_fields:
            from datetime import datetime
            session.last_accessed = datetime.utcnow()
            db.session.commit()
            
            # Log session update
            from ..models.audit import AuditLog
            AuditLog.log_session_event(
                'session_updated',
                session,
                user=user,
                message=f"Session updated: {', '.join(updated_fields)}"
            )
            
            logger.info(f"Updated session {session_id}: {', '.join(updated_fields)}")
        
        return success_response(
            'Session updated successfully' if updated_fields else 'No changes made',
            {
                'session': session.to_dict(),
                'updated_fields': updated_fields
            }
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Session update error: {e}")
        return error_response(
            'session_update_failed',
            'Failed to update session'
        ), 500

@sessions_bp.route('/<session_id>/extend', methods=['POST'])
@auth_required()
@validate_user_ownership('session_id', BrowserSession)
@rate_limit("5 per hour")
@log_api_call()
def extend_session(session_id):
    """Extend session expiration time"""
    try:
        session = g.resource
        user = g.current_user
        
        # Get extension hours from request (default 1 hour)
        data = request.get_json() or {}
        hours = min(int(data.get('hours', 1)), 8)  # Max 8 hours extension
        
        if not session.is_active:
            return error_response(
                'session_not_active',
                'Cannot extend inactive session'
            ), 400
        
        # Extend session
        session.extend_session(hours)
        
        # Log session extension
        from ..models.audit import AuditLog
        AuditLog.log_session_event(
            'session_extended',
            session,
            user=user,
            message=f"Session extended by {hours} hours"
        )
        
        logger.info(f"Extended session {session_id} by {hours} hours")
        
        return success_response(
            f'Session extended by {hours} hours',
            {
                'session': session.to_dict(),
                'extended_hours': hours
            }
        )
        
    except Exception as e:
        logger.error(f"Session extension error: {e}")
        return error_response(
            'session_extension_failed',
            'Failed to extend session'
        ), 500

@sessions_bp.route('/<session_id>/stop', methods=['POST'])
@auth_required()
@validate_user_ownership('session_id', BrowserSession)
@log_api_call()
def stop_session(session_id):
    """Stop a browser session"""
    try:
        session = g.resource
        user = g.current_user
        
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
        session.update_status(SessionStatus.STOPPED)
        
        # Log session stop
        from ..models.audit import AuditLog
        AuditLog.log_session_event(
            'session_stopped',
            session,
            user=user,
            message=f"Session stopped: {session.session_name}"
        )
        
        logger.info(f"Stopped session {session_id}")
        
        return success_response(
            'Session stopped successfully',
            {'session': session.to_dict()}
        )
        
    except Exception as e:
        logger.error(f"Session stop error: {e}")
        return error_response(
            'session_stop_failed',
            'Failed to stop session'
        ), 500

@sessions_bp.route('/<session_id>', methods=['DELETE'])
@auth_required()
@validate_user_ownership('session_id', BrowserSession)
@log_api_call()
def delete_session(session_id):
    """Delete a browser session"""
    try:
        session = g.resource
        user = g.current_user
        
        # Stop and remove container if exists
        if session.container_id:
            docker_service.stop_container(session.container_id)
            docker_service.remove_container(session.container_id, force=True)
        
        # Delete session record
        db.session.delete(session)
        db.session.commit()
        
        # Log session deletion
        from ..models.audit import AuditLog
        AuditLog.log_event(
            'session_deleted',
            user=user,
            resource_type='session',
            resource_id=session_id,
            message=f"Session deleted: {session.session_name}"
        )
        
        logger.info(f"Deleted session {session_id}")
        
        return success_response('Session deleted successfully')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Session deletion error: {e}")
        return error_response(
            'session_deletion_failed',
            'Failed to delete session'
        ), 500

@sessions_bp.route('/<session_id>/access', methods=['POST'])
@auth_required()
@validate_user_ownership('session_id', BrowserSession)
@log_api_call()
def access_session(session_id):
    """Record session access and return connection info"""
    try:
        session = g.resource
        
        if not session.is_active:
            return error_response(
                'session_not_active',
                'Session is not currently active'
            ), 400
        
        # Check if session has expired
        if session.is_expired:
            # Auto-stop expired session
            session.update_status(SessionStatus.EXPIRED)
            return error_response(
                'session_expired',
                'Session has expired'
            ), 410
        
        # Update access time and increment page views
        session.increment_page_views()
        
        # Get container status
        container_status = {}
        if session.container_id:
            container_status = docker_service.get_container_status(session.container_id)
        
        return success_response(
            'Session access recorded',
            {
                'session': session.to_dict(),
                'container_status': container_status,
                'connection_info': {
                    'access_url': session.access_url,
                    'vnc_port': session.vnc_port,
                    'web_port': session.web_port,
                    'time_remaining': session.time_remaining
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Session access error: {e}")
        return error_response(
            'session_access_failed',
            'Failed to access session'
        ), 500

@sessions_bp.route('/cleanup', methods=['POST'])
@auth_required()
@rate_limit("1 per hour")
@log_api_call()
def cleanup_user_sessions():
    """Clean up expired sessions for current user"""
    try:
        user = g.current_user
        
        from datetime import datetime, timedelta
        
        # Find expired sessions
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        expired_sessions = user.browser_sessions.filter(
            BrowserSession.expires_at < datetime.utcnow(),
            BrowserSession.status.in_([SessionStatus.RUNNING, SessionStatus.CREATING])
        ).all()
        
        cleaned_count = 0
        for session in expired_sessions:
            try:
                # Stop and remove container
                if session.container_id:
                    docker_service.stop_container(session.container_id)
                    docker_service.remove_container(session.container_id, force=True)
                
                # Update session status
                session.update_status(SessionStatus.EXPIRED)
                cleaned_count += 1
                
            except Exception as e:
                logger.error(f"Error cleaning session {session.id}: {e}")
        
        db.session.commit()
        
        logger.info(f"Cleaned up {cleaned_count} expired sessions for user {user.username}")
        
        return success_response(
            f'Cleaned up {cleaned_count} expired sessions',
            {'cleaned_sessions': cleaned_count}
        )
        
    except Exception as e:
        logger.error(f"Session cleanup error: {e}")
        return error_response(
            'cleanup_failed',
            'Failed to clean up sessions'
        ), 500

# Error handlers for sessions blueprint
@sessions_bp.errorhandler(404)
def session_not_found(error):
    return error_response(
        'session_not_found',
        'The requested session was not found'
    ), 404

@sessions_bp.errorhandler(410)
def session_expired(error):
    return error_response(
        'session_expired',
        'The session has expired and is no longer available'
    ), 410

@sessions_bp.errorhandler(503)
def service_unavailable(error):
    return error_response(
        'service_unavailable',
        'The container service is temporarily unavailable'
    ), 503
