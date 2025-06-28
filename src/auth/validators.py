"""
Input validation utilities for authentication
"""
import re
from typing import Dict, List, Any
from email_validator import validate_email as _validate_email, EmailNotValidError

def validate_email(email: str) -> Dict[str, Any]:
    """
    Validate email address format and deliverability
    
    Args:
        email: Email address to validate
        
    Returns:
        Dictionary with validation results
    """
    if not email:
        return {
            'valid': False,
            'normalized': None,
            'errors': ['Email is required']
        }
    
    try:
        # Use email-validator library for comprehensive validation
        validated_email = _validate_email(
            email,
            check_deliverability=False  # Disable DNS checks for faster validation
        )
        
        return {
            'valid': True,
            'normalized': validated_email.email,
            'local': validated_email.local,
            'domain': validated_email.domain,
            'errors': []
        }
    
    except EmailNotValidError as e:
        return {
            'valid': False,
            'normalized': None,
            'errors': [str(e)]
        }

def validate_password(password: str, username: str = None, email: str = None) -> Dict[str, Any]:
    """
    Comprehensive password validation
    
    Args:
        password: Password to validate
        username: Username to check for similarity (optional)
        email: Email to check for similarity (optional)
        
    Returns:
        Dictionary with validation results
    """
    from .security import security_manager
    
    # Use security manager for password strength check
    result = security_manager.check_password_strength(password)
    
    # Additional checks for similarity with username/email
    if result['valid'] and (username or email):
        password_lower = password.lower()
        
        # Check similarity with username
        if username and len(username) >= 3:
            if username.lower() in password_lower or password_lower in username.lower():
                result['valid'] = False
                result['errors'].append('Password cannot be similar to username')
        
        # Check similarity with email
        if email and len(email) >= 3:
            email_local = email.split('@')[0].lower()
            if email_local in password_lower or password_lower in email_local:
                result['valid'] = False
                result['errors'].append('Password cannot be similar to email')
    
    return result

def validate_username(username: str) -> Dict[str, Any]:
    """
    Validate username format and requirements
    
    Args:
        username: Username to validate
        
    Returns:
        Dictionary with validation results
    """
    errors = []
    
    if not username:
        return {
            'valid': False,
            'errors': ['Username is required']
        }
    
    # Length check
    if len(username) < 3:
        errors.append('Username must be at least 3 characters long')
    
    if len(username) > 30:
        errors.append('Username must be no more than 30 characters long')
    
    # Character validation
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        errors.append('Username can only contain letters, numbers, dots, underscores, and hyphens')
    
    # Cannot start or end with special characters
    if username and username[0] in '._-':
        errors.append('Username cannot start with a special character')
    
    if username and username[-1] in '._-':
        errors.append('Username cannot end with a special character')
    
    # Cannot have consecutive special characters
    if re.search(r'[._-]{2,}', username):
        errors.append('Username cannot have consecutive special characters')
    
    # Reserved usernames
    reserved_usernames = [
        'admin', 'administrator', 'root', 'system', 'user', 'guest',
        'api', 'www', 'mail', 'email', 'support', 'help', 'info',
        'test', 'demo', 'null', 'undefined', 'anonymous'
    ]
    
    if username.lower() in reserved_usernames:
        errors.append('This username is reserved and cannot be used')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_name(name: str, field_name: str = 'Name') -> Dict[str, Any]:
    """
    Validate first name or last name
    
    Args:
        name: Name to validate
        field_name: Field name for error messages
        
    Returns:
        Dictionary with validation results
    """
    errors = []
    
    if name is None:
        name = ''
    
    # Length check (optional field, so empty is allowed)
    if name and len(name) < 2:
        errors.append(f'{field_name} must be at least 2 characters long')
    
    if len(name) > 50:
        errors.append(f'{field_name} must be no more than 50 characters long')
    
    # Character validation (only letters, spaces, hyphens, apostrophes)
    if name and not re.match(r"^[a-zA-Z\s\-']+$", name):
        errors.append(f'{field_name} can only contain letters, spaces, hyphens, and apostrophes')
    
    # Cannot start or end with special characters
    if name and name[0] in " -'":
        errors.append(f'{field_name} cannot start with a special character')
    
    if name and name[-1] in " -'":
        errors.append(f'{field_name} cannot end with a special character')
    
    return {
        'valid': len(errors) == 0,
        'normalized': name.strip().title() if name else '',
        'errors': errors
    }

def validate_registration_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complete registration data
    
    Args:
        data: Dictionary containing registration data
        
    Returns:
        Dictionary with validation results
    """
    errors = {}
    valid_data = {}
    
    # Validate email
    email_result = validate_email(data.get('email', ''))
    if not email_result['valid']:
        errors['email'] = email_result['errors']
    else:
        valid_data['email'] = email_result['normalized']
    
    # Validate username
    username_result = validate_username(data.get('username', ''))
    if not username_result['valid']:
        errors['username'] = username_result['errors']
    else:
        valid_data['username'] = data.get('username', '').strip()
    
    # Validate password
    password_result = validate_password(
        data.get('password', ''),
        username=data.get('username'),
        email=data.get('email')
    )
    if not password_result['valid']:
        errors['password'] = password_result['errors']
    else:
        valid_data['password'] = data.get('password')
    
    # Validate password confirmation
    password_confirm = data.get('password_confirm')
    if password_confirm != data.get('password'):
        errors['password_confirm'] = ['Passwords do not match']
    
    # Validate first name (optional)
    first_name = data.get('first_name', '')
    if first_name:
        first_name_result = validate_name(first_name, 'First name')
        if not first_name_result['valid']:
            errors['first_name'] = first_name_result['errors']
        else:
            valid_data['first_name'] = first_name_result['normalized']
    
    # Validate last name (optional)
    last_name = data.get('last_name', '')
    if last_name:
        last_name_result = validate_name(last_name, 'Last name')
        if not last_name_result['valid']:
            errors['last_name'] = last_name_result['errors']
        else:
            valid_data['last_name'] = last_name_result['normalized']
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'data': valid_data
    }

def validate_login_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate login data
    
    Args:
        data: Dictionary containing login data
        
    Returns:
        Dictionary with validation results
    """
    errors = {}
    valid_data = {}
    
    # Validate email/username
    identifier = data.get('email') or data.get('username')
    if not identifier:
        errors['email'] = ['Email or username is required']
    else:
        valid_data['identifier'] = identifier.strip()
    
    # Validate password
    password = data.get('password')
    if not password:
        errors['password'] = ['Password is required']
    else:
        valid_data['password'] = password
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'data': valid_data
    }

def validate_session_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate browser session creation data
    
    Args:
        data: Dictionary containing session data
        
    Returns:
        Dictionary with validation results
    """
    errors = {}
    valid_data = {}
    
    # Validate browser type
    browser_type = data.get('browser_type', 'firefox')
    valid_browsers = ['firefox', 'chrome', 'chromium']
    if browser_type not in valid_browsers:
        errors['browser_type'] = [f'Browser type must be one of: {", ".join(valid_browsers)}']
    else:
        valid_data['browser_type'] = browser_type
    
    # Validate session name (optional)
    session_name = data.get('session_name', '')
    if session_name:
        if len(session_name) > 100:
            errors['session_name'] = ['Session name must be no more than 100 characters']
        elif not re.match(r'^[a-zA-Z0-9\s._-]+$', session_name):
            errors['session_name'] = ['Session name contains invalid characters']
        else:
            valid_data['session_name'] = session_name.strip()
    
    # Validate initial URL (optional)
    initial_url = data.get('initial_url', '')
    if initial_url:
        from .security import security_manager
        if not security_manager.validate_url(initial_url):
            errors['initial_url'] = ['Invalid or unsafe URL']
        else:
            valid_data['initial_url'] = initial_url
    
    # Validate screen resolution (optional)
    screen_resolution = data.get('screen_resolution', '1920x1080')
    if not re.match(r'^\d{3,4}x\d{3,4}$', screen_resolution):
        errors['screen_resolution'] = ['Invalid screen resolution format (e.g., 1920x1080)']
    else:
        valid_data['screen_resolution'] = screen_resolution
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'data': valid_data
    }

def validate_github_url(url: str) -> Dict[str, Any]:
    """
    Validate GitHub repository URL
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Dictionary with validation results
    """
    if not url:
        return {
            'valid': False,
            'errors': ['GitHub URL is required']
        }
    
    # GitHub URL patterns
    github_patterns = [
        r'^https://github\.com/[a-zA-Z0-9\-_\.]+/[a-zA-Z0-9\-_\.]+/?$',
        r'^git@github\.com:[a-zA-Z0-9\-_\.]+/[a-zA-Z0-9\-_\.]+\.git$'
    ]
    
    valid = any(re.match(pattern, url) for pattern in github_patterns)
    
    if not valid:
        return {
            'valid': False,
            'errors': ['Invalid GitHub repository URL format']
        }
    
    # Extract owner and repo name
    if url.startswith('https://'):
        parts = url.rstrip('/').split('/')
        if len(parts) >= 5:
            owner = parts[-2]
            repo = parts[-1]
        else:
            return {
                'valid': False,
                'errors': ['Could not parse repository owner and name from URL']
            }
    else:  # SSH format
        # git@github.com:owner/repo.git
        try:
            path_part = url.split(':')[1]  # owner/repo.git
            owner, repo_with_git = path_part.split('/')
            repo = repo_with_git.replace('.git', '')
        except Exception:
            return {
                'valid': False,
                'errors': ['Could not parse repository owner and name from SSH URL']
            }
    
    return {
        'valid': True,
        'owner': owner,
        'repo': repo,
        'normalized_url': f'https://github.com/{owner}/{repo}',
        'errors': []
    }
