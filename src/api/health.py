"""
Health check API endpoints
"""
from flask import Blueprint, jsonify
import logging
from datetime import datetime

from ..services.docker_service import docker_service
from ..services.kimi_service import kimi_service
from ..models.user import db
from ..utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create health blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        return success_response(
            'Service is healthy',
            {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0'
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return error_response(
            'service_unhealthy',
            'Service health check failed'
        ), 503

@health_bp.route('/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with component status"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'components': {}
        }
        
        overall_healthy = True
        
        # Check database
        try:
            db.session.execute('SELECT 1')
            health_status['components']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
            overall_healthy = False
        
        # Check Docker service
        try:
            if docker_service.is_available():
                docker_info = docker_service.get_system_resources()
                health_status['components']['docker'] = {
                    'status': 'healthy',
                    'message': 'Docker service available',
                    'info': {
                        'containers_running': docker_info.get('containers_running', 0),
                        'containers_total': docker_info.get('containers_total', 0),
                        'docker_version': docker_info.get('docker_version', 'unknown')
                    }
                }
            else:
                health_status['components']['docker'] = {
                    'status': 'unhealthy',
                    'message': 'Docker service unavailable'
                }
                overall_healthy = False
        except Exception as e:
            health_status['components']['docker'] = {
                'status': 'unhealthy',
                'message': f'Docker service error: {str(e)}'
            }
            overall_healthy = False
        
        # Check Kimi-Dev service
        try:
            if kimi_service.is_available():
                health_status['components']['kimi_dev'] = {
                    'status': 'healthy',
                    'message': 'Kimi-Dev service available'
                }
            else:
                health_status['components']['kimi_dev'] = {
                    'status': 'degraded',
                    'message': 'Kimi-Dev service unavailable (optional)'
                }
                # Don't mark overall as unhealthy since this is optional
        except Exception as e:
            health_status['components']['kimi_dev'] = {
                'status': 'degraded',
                'message': f'Kimi-Dev service error: {str(e)} (optional)'
            }
        
        # Set overall status
        health_status['status'] = 'healthy' if overall_healthy else 'unhealthy'
        
        status_code = 200 if overall_healthy else 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return error_response(
            'health_check_failed',
            'Detailed health check failed'
        ), 503

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check for Kubernetes/deployment"""
    try:
        # Check critical components only
        critical_healthy = True
        
        # Check database
        try:
            db.session.execute('SELECT 1')
        except Exception:
            critical_healthy = False
        
        # Check Docker service
        try:
            if not docker_service.is_available():
                critical_healthy = False
        except Exception:
            critical_healthy = False
        
        if critical_healthy:
            return success_response(
                'Service is ready',
                {
                    'status': 'ready',
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        else:
            return error_response(
                'service_not_ready',
                'Service is not ready'
            ), 503
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return error_response(
            'readiness_check_failed',
            'Readiness check failed'
        ), 503

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """Liveness check for Kubernetes/deployment"""
    try:
        # Basic liveness check - just return success if the service is running
        return success_response(
            'Service is alive',
            {
                'status': 'alive',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return error_response(
            'liveness_check_failed',
            'Liveness check failed'
        ), 503

@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """Basic metrics endpoint"""
    try:
        from ..models.session import BrowserSession, SessionStatus
        from ..models.user import User
        from sqlalchemy import func
        
        # Get basic metrics
        metrics_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'users': {
                'total': User.query.count(),
                'active': User.query.filter_by(active=True).count()
            },
            'sessions': {
                'total': BrowserSession.query.count(),
                'running': BrowserSession.query.filter_by(status=SessionStatus.RUNNING).count(),
                'creating': BrowserSession.query.filter_by(status=SessionStatus.CREATING).count(),
                'stopped': BrowserSession.query.filter_by(status=SessionStatus.STOPPED).count()
            }
        }
        
        # Add Docker metrics if available
        if docker_service.is_available():
            docker_info = docker_service.get_system_resources()
            metrics_data['docker'] = {
                'containers_running': docker_info.get('containers_running', 0),
                'containers_total': docker_info.get('containers_total', 0),
                'images_count': docker_info.get('images_count', 0)
            }
        
        return success_response(
            'Metrics retrieved successfully',
            metrics_data
        )
        
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        return error_response(
            'metrics_failed',
            'Failed to retrieve metrics'
        ), 500

# No authentication required for health endpoints
# These are typically used by load balancers and monitoring systems
