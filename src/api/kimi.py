"""
Kimi-Dev-72B integration API endpoints
"""
from flask import Blueprint, request, jsonify, g
import logging

from ..auth.decorators import auth_required, validate_json, rate_limit, log_api_call
from ..auth.validators import validate_github_url
from ..services.kimi_service import kimi_service
from ..utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create kimi blueprint
kimi_bp = Blueprint('kimi', __name__)

@kimi_bp.route('/analyze/repository', methods=['POST'])
@auth_required()
@rate_limit("5 per hour")
@validate_json(['github_url'])
@log_api_call()
def analyze_repository():
    """Analyze a GitHub repository for issues and suggestions"""
    try:
        user = g.current_user
        data = g.json_data
        
        # Validate GitHub URL
        url_validation = validate_github_url(data['github_url'])
        if not url_validation['valid']:
            return error_response(
                'validation_failed',
                'GitHub URL validation failed',
                {'github_url': url_validation['errors']}
            ), 400
        
        # Check if Kimi-Dev service is available
        if not kimi_service.is_available():
            return error_response(
                'service_unavailable',
                'Kimi-Dev analysis service is not available'
            ), 503
        
        # Perform repository analysis
        result = kimi_service.analyze_repository(
            github_url=data['github_url'],
            issue_description=data.get('issue_description'),
            commit_hash=data.get('commit_hash')
        )
        
        if result['success']:
            # Log analysis request
            from ..models.audit import AuditLog
            AuditLog.log_event(
                'kimi_analysis_request',
                user=user,
                request=request,
                message=f"Repository analysis requested: {url_validation['normalized_url']}",
                metadata={
                    'repository': url_validation,
                    'analysis_id': result.get('analysis_id')
                }
            )
            
            logger.info(f"User {user.username} requested repository analysis: {data['github_url']}")
            
            return success_response(
                'Repository analysis completed',
                {
                    'analysis': result,
                    'repository': url_validation
                }
            )
        else:
            return error_response(
                'analysis_failed',
                result['error'],
                result.get('details')
            ), 500
            
    except Exception as e:
        logger.error(f"Repository analysis error: {e}")
        return error_response(
            'analysis_service_error',
            'Repository analysis service error'
        ), 500

@kimi_bp.route('/analyze/code', methods=['POST'])
@auth_required()
@rate_limit("10 per hour")
@validate_json(['code', 'language'])
@log_api_call()
def analyze_code():
    """Analyze a code snippet for issues and improvements"""
    try:
        user = g.current_user
        data = g.json_data
        
        # Validate input
        if not data['code'].strip():
            return error_response(
                'validation_failed',
                'Code snippet cannot be empty'
            ), 400
        
        # Check if Kimi-Dev service is available
        if not kimi_service.is_available():
            return error_response(
                'service_unavailable',
                'Kimi-Dev analysis service is not available'
            ), 503
        
        # Get supported languages
        supported_languages = kimi_service.get_supported_languages()
        if data['language'] not in supported_languages:
            return error_response(
                'unsupported_language',
                f'Language "{data["language"]}" is not supported',
                {'supported_languages': supported_languages}
            ), 400
        
        # Perform code analysis
        result = kimi_service.analyze_code_snippet(
            code=data['code'],
            language=data['language'],
            issue_description=data.get('issue_description')
        )
        
        if result['success']:
            # Log analysis request
            from ..models.audit import AuditLog
            AuditLog.log_event(
                'kimi_code_analysis',
                user=user,
                request=request,
                message=f"Code analysis requested for {data['language']}",
                metadata={
                    'language': data['language'],
                    'code_length': len(data['code']),
                    'analysis_id': result.get('analysis_id')
                }
            )
            
            logger.info(f"User {user.username} requested code analysis for {data['language']}")
            
            return success_response(
                'Code analysis completed',
                {'analysis': result}
            )
        else:
            return error_response(
                'analysis_failed',
                result['error'],
                result.get('details')
            ), 500
            
    except Exception as e:
        logger.error(f"Code analysis error: {e}")
        return error_response(
            'analysis_service_error',
            'Code analysis service error'
        ), 500

@kimi_bp.route('/debug', methods=['POST'])
@auth_required()
@rate_limit("10 per hour")
@validate_json(['error_message'])
@log_api_call()
def debug_issue():
    """Debug a specific issue with error message and context"""
    try:
        user = g.current_user
        data = g.json_data
        
        # Validate input
        if not data['error_message'].strip():
            return error_response(
                'validation_failed',
                'Error message cannot be empty'
            ), 400
        
        # Check if Kimi-Dev service is available
        if not kimi_service.is_available():
            return error_response(
                'service_unavailable',
                'Kimi-Dev debug service is not available'
            ), 503
        
        # Perform debugging
        result = kimi_service.debug_issue(
            error_message=data['error_message'],
            code_context=data.get('code_context'),
            stack_trace=data.get('stack_trace'),
            language=data.get('language')
        )
        
        if result['success']:
            # Log debug request
            from ..models.audit import AuditLog
            AuditLog.log_event(
                'kimi_debug_request',
                user=user,
                request=request,
                message=f"Debug assistance requested",
                metadata={
                    'language': data.get('language'),
                    'has_context': bool(data.get('code_context')),
                    'has_stack_trace': bool(data.get('stack_trace')),
                    'debug_id': result.get('debug_id')
                }
            )
            
            logger.info(f"User {user.username} requested debug assistance")
            
            return success_response(
                'Debug analysis completed',
                {'debug': result}
            )
        else:
            return error_response(
                'debug_failed',
                result['error'],
                result.get('details')
            ), 500
            
    except Exception as e:
        logger.error(f"Debug service error: {e}")
        return error_response(
            'debug_service_error',
            'Debug service error'
        ), 500

@kimi_bp.route('/analyze/file', methods=['POST'])
@auth_required()
@rate_limit("10 per hour")
@validate_json(['file_path', 'file_content'])
@log_api_call()
def analyze_file():
    """Get suggestions for a specific file"""
    try:
        user = g.current_user
        data = g.json_data
        
        # Validate input
        if not data['file_content'].strip():
            return error_response(
                'validation_failed',
                'File content cannot be empty'
            ), 400
        
        # Check if Kimi-Dev service is available
        if not kimi_service.is_available():
            return error_response(
                'service_unavailable',
                'Kimi-Dev analysis service is not available'
            ), 503
        
        # Perform file analysis
        result = kimi_service.get_file_suggestions(
            file_path=data['file_path'],
            file_content=data['file_content'],
            language=data.get('language')
        )
        
        if result['success']:
            # Log analysis request
            from ..models.audit import AuditLog
            AuditLog.log_event(
                'kimi_file_analysis',
                user=user,
                request=request,
                message=f"File analysis requested: {data['file_path']}",
                metadata={
                    'file_path': data['file_path'],
                    'language': result.get('language'),
                    'content_length': len(data['file_content'])
                }
            )
            
            logger.info(f"User {user.username} requested file analysis: {data['file_path']}")
            
            return success_response(
                'File analysis completed',
                {'analysis': result}
            )
        else:
            return error_response(
                'analysis_failed',
                result['error'],
                result.get('details')
            ), 500
            
    except Exception as e:
        logger.error(f"File analysis error: {e}")
        return error_response(
            'analysis_service_error',
            'File analysis service error'
        ), 500

@kimi_bp.route('/analysis/<analysis_id>/status', methods=['GET'])
@auth_required()
@log_api_call()
def get_analysis_status(analysis_id):
    """Get the status of an ongoing analysis"""
    try:
        # Check if Kimi-Dev service is available
        if not kimi_service.is_available():
            return error_response(
                'service_unavailable',
                'Kimi-Dev analysis service is not available'
            ), 503
        
        # Get analysis status
        result = kimi_service.get_analysis_status(analysis_id)
        
        if result['success']:
            return success_response(
                'Analysis status retrieved',
                {'status': result}
            )
        else:
            return error_response(
                'status_retrieval_failed',
                result['error']
            ), 404
            
    except Exception as e:
        logger.error(f"Analysis status error: {e}")
        return error_response(
            'status_service_error',
            'Analysis status service error'
        ), 500

@kimi_bp.route('/analysis/<analysis_id>/results', methods=['GET'])
@auth_required()
@log_api_call()
def get_analysis_results(analysis_id):
    """Get the results of a completed analysis"""
    try:
        # Check if Kimi-Dev service is available
        if not kimi_service.is_available():
            return error_response(
                'service_unavailable',
                'Kimi-Dev analysis service is not available'
            ), 503
        
        # Get analysis results
        result = kimi_service.get_analysis_results(analysis_id)
        
        if result['success']:
            return success_response(
                'Analysis results retrieved',
                {'results': result['results']}
            )
        else:
            return error_response(
                'results_retrieval_failed',
                result['error']
            ), 404
            
    except Exception as e:
        logger.error(f"Analysis results error: {e}")
        return error_response(
            'results_service_error',
            'Analysis results service error'
        ), 500

@kimi_bp.route('/languages', methods=['GET'])
@auth_required()
@log_api_call()
def get_supported_languages():
    """Get list of supported programming languages"""
    try:
        languages = kimi_service.get_supported_languages()
        
        return success_response(
            'Supported languages retrieved',
            {'languages': languages}
        )
        
    except Exception as e:
        logger.error(f"Languages retrieval error: {e}")
        return error_response(
            'languages_service_error',
            'Failed to retrieve supported languages'
        ), 500

@kimi_bp.route('/session', methods=['POST'])
@auth_required()
@rate_limit("5 per hour")
@log_api_call()
def create_analysis_session():
    """Create a new analysis session"""
    try:
        user = g.current_user
        
        # Check if Kimi-Dev service is available
        if not kimi_service.is_available():
            return error_response(
                'service_unavailable',
                'Kimi-Dev analysis service is not available'
            ), 503
        
        # Create analysis session
        result = kimi_service.create_analysis_session(user.id)
        
        if result['success']:
            # Log session creation
            from ..models.audit import AuditLog
            AuditLog.log_event(
                'kimi_session_created',
                user=user,
                request=request,
                message=f"Analysis session created",
                metadata={
                    'session_id': result.get('session_id')
                }
            )
            
            logger.info(f"User {user.username} created analysis session")
            
            return success_response(
                'Analysis session created',
                {'session': result}
            ), 201
        else:
            return error_response(
                'session_creation_failed',
                result['error'],
                result.get('details')
            ), 500
            
    except Exception as e:
        logger.error(f"Analysis session creation error: {e}")
        return error_response(
            'session_service_error',
            'Analysis session creation service error'
        ), 500

# Error handlers for kimi blueprint
@kimi_bp.errorhandler(503)
def service_unavailable(error):
    return error_response(
        'service_unavailable',
        'The Kimi-Dev analysis service is temporarily unavailable'
    ), 503

@kimi_bp.errorhandler(413)
def payload_too_large(error):
    return error_response(
        'payload_too_large',
        'The code snippet or file content is too large to analyze'
    ), 413
