"""
Response helper functions for consistent API responses
"""
from flask import jsonify
from typing import Any, Dict, Optional, Union
from datetime import datetime

def success_response(message: str, data: Optional[Dict[str, Any]] = None, 
                    meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a standardized success response
    
    Args:
        message: Success message
        data: Response data (optional)
        meta: Metadata (optional)
        
    Returns:
        Standardized success response dictionary
    """
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    if meta is not None:
        response['meta'] = meta
    
    return jsonify(response)

def error_response(error_code: str, message: str, 
                  details: Optional[Union[str, Dict[str, Any]]] = None,
                  meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a standardized error response
    
    Args:
        error_code: Error code identifier
        message: Error message
        details: Error details (optional)
        meta: Metadata (optional)
        
    Returns:
        Standardized error response dictionary
    """
    response = {
        'success': False,
        'error': {
            'code': error_code,
            'message': message
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details is not None:
        response['error']['details'] = details
    
    if meta is not None:
        response['meta'] = meta
    
    return jsonify(response)

def paginated_response(message: str, items: list, pagination: Dict[str, Any],
                      meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a standardized paginated response
    
    Args:
        message: Success message
        items: List of items for current page
        pagination: Pagination information
        meta: Additional metadata (optional)
        
    Returns:
        Standardized paginated response dictionary
    """
    data = {
        'items': items,
        'pagination': pagination
    }
    
    return success_response(message, data, meta)

def validation_error_response(validation_errors: Dict[str, list]) -> Dict[str, Any]:
    """
    Create a standardized validation error response
    
    Args:
        validation_errors: Dictionary of field validation errors
        
    Returns:
        Standardized validation error response dictionary
    """
    return error_response(
        'validation_failed',
        'Request validation failed',
        validation_errors
    )

def not_found_response(resource_type: str = 'Resource') -> Dict[str, Any]:
    """
    Create a standardized not found response
    
    Args:
        resource_type: Type of resource that was not found
        
    Returns:
        Standardized not found response dictionary
    """
    return error_response(
        'not_found',
        f'{resource_type} not found'
    )

def unauthorized_response(message: str = 'Authentication required') -> Dict[str, Any]:
    """
    Create a standardized unauthorized response
    
    Args:
        message: Unauthorized message
        
    Returns:
        Standardized unauthorized response dictionary
    """
    return error_response(
        'unauthorized',
        message
    )

def forbidden_response(message: str = 'Access denied') -> Dict[str, Any]:
    """
    Create a standardized forbidden response
    
    Args:
        message: Forbidden message
        
    Returns:
        Standardized forbidden response dictionary
    """
    return error_response(
        'forbidden',
        message
    )

def rate_limit_response(limit: str = 'Rate limit exceeded') -> Dict[str, Any]:
    """
    Create a standardized rate limit response
    
    Args:
        limit: Rate limit information
        
    Returns:
        Standardized rate limit response dictionary
    """
    return error_response(
        'rate_limit_exceeded',
        f'Rate limit exceeded: {limit}'
    )

def service_unavailable_response(service: str = 'Service') -> Dict[str, Any]:
    """
    Create a standardized service unavailable response
    
    Args:
        service: Name of the unavailable service
        
    Returns:
        Standardized service unavailable response dictionary
    """
    return error_response(
        'service_unavailable',
        f'{service} is temporarily unavailable'
    )

def internal_error_response(message: str = 'Internal server error') -> Dict[str, Any]:
    """
    Create a standardized internal server error response
    
    Args:
        message: Error message
        
    Returns:
        Standardized internal error response dictionary
    """
    return error_response(
        'internal_server_error',
        message
    )

def create_response_with_status(response_func, status_code: int):
    """
    Create a response with a specific status code
    
    Args:
        response_func: Response function to call
        status_code: HTTP status code
        
    Returns:
        Tuple of (response, status_code)
    """
    response = response_func()
    return response, status_code

# Common HTTP status codes for convenience
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
HTTP_410_GONE = 410
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_429_TOO_MANY_REQUESTS = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_503_SERVICE_UNAVAILABLE = 503

# Response format examples for documentation
RESPONSE_EXAMPLES = {
    'success': {
        'success': True,
        'message': 'Operation completed successfully',
        'data': {
            'key': 'value'
        },
        'timestamp': '2023-12-06T10:30:00.000Z'
    },
    'error': {
        'success': False,
        'error': {
            'code': 'error_code',
            'message': 'Error description',
            'details': {
                'field': ['Field specific error message']
            }
        },
        'timestamp': '2023-12-06T10:30:00.000Z'
    },
    'paginated': {
        'success': True,
        'message': 'Items retrieved successfully',
        'data': {
            'items': [],
            'pagination': {
                'page': 1,
                'per_page': 20,
                'total': 100,
                'pages': 5,
                'has_prev': False,
                'has_next': True
            }
        },
        'timestamp': '2023-12-06T10:30:00.000Z'
    }
}
