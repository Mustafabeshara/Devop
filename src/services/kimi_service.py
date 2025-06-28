"""
Kimi-Dev-72B integration service for code analysis and debugging
"""
import requests
import json
import logging
import time
from typing import Dict, List, Optional, Any, Generator
from datetime import datetime
from flask import current_app
import re
from urllib.parse import urlparse
import base64

logger = logging.getLogger(__name__)

class KimiDevService:
    """Service for integrating with Kimi-Dev-72B model"""
    
    def __init__(self):
        self.api_url = None
        self.api_key = None
        self.session = requests.Session()
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Kimi-Dev service configuration"""
        self.api_url = current_app.config.get('KIMI_DEV_API_URL', 'http://localhost:8000')
        self.api_key = current_app.config.get('KIMI_DEV_API_KEY', '')
        
        # Set up session headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Cloud-Browser-Service/1.0'
        })
        
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
            })
    
    def is_available(self) -> bool:
        """Check if Kimi-Dev service is available"""
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def analyze_repository(self, github_url: str, issue_description: str = None, 
                          commit_hash: str = None) -> Dict[str, Any]:
        """
        Analyze a GitHub repository for issues and suggestions
        
        Args:
            github_url: GitHub repository URL
            issue_description: Description of the issue to analyze
            commit_hash: Specific commit to analyze (optional)
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Parse GitHub URL
            repo_info = self._parse_github_url(github_url)
            if not repo_info['valid']:
                return {
                    'success': False,
                    'error': 'Invalid GitHub URL',
                    'details': repo_info['errors']
                }
            
            # Prepare analysis request
            analysis_request = {
                'repository': {
                    'url': github_url,
                    'owner': repo_info['owner'],
                    'name': repo_info['repo'],
                    'commit_hash': commit_hash
                },
                'analysis_type': 'repository_scan',
                'options': {
                    'include_suggestions': True,
                    'analyze_dependencies': True,
                    'check_security': True,
                    'performance_analysis': True
                }
            }
            
            if issue_description:
                analysis_request['issue_description'] = issue_description
            
            # Send analysis request
            response = self.session.post(
                f"{self.api_url}/api/v1/analyze/repository",
                json=analysis_request,
                timeout=300  # 5 minutes timeout for repository analysis
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'analysis_id': result.get('analysis_id'),
                    'repository': repo_info,
                    'findings': result.get('findings', []),
                    'suggestions': result.get('suggestions', []),
                    'file_analysis': result.get('file_analysis', {}),
                    'security_issues': result.get('security_issues', []),
                    'performance_issues': result.get('performance_issues', []),
                    'summary': result.get('summary', ''),
                    'confidence_score': result.get('confidence_score', 0),
                    'analyzed_at': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'Analysis failed with status {response.status_code}',
                    'details': response.text
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Analysis request timed out',
                'details': 'The repository analysis took too long to complete'
            }
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            return {
                'success': False,
                'error': 'Analysis service error',
                'details': str(e)
            }
    
    def analyze_code_snippet(self, code: str, language: str, 
                           issue_description: str = None) -> Dict[str, Any]:
        """
        Analyze a specific code snippet
        
        Args:
            code: Code snippet to analyze
            language: Programming language
            issue_description: Description of the issue (optional)
            
        Returns:
            Analysis results dictionary
        """
        try:
            analysis_request = {
                'code': code,
                'language': language,
                'analysis_type': 'code_snippet',
                'options': {
                    'syntax_check': True,
                    'security_scan': True,
                    'performance_analysis': True,
                    'best_practices': True,
                    'suggest_improvements': True
                }
            }
            
            if issue_description:
                analysis_request['issue_description'] = issue_description
            
            response = self.session.post(
                f"{self.api_url}/api/v1/analyze/code",
                json=analysis_request,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'analysis_id': result.get('analysis_id'),
                    'issues': result.get('issues', []),
                    'suggestions': result.get('suggestions', []),
                    'improved_code': result.get('improved_code', ''),
                    'explanation': result.get('explanation', ''),
                    'confidence_score': result.get('confidence_score', 0),
                    'analyzed_at': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'Code analysis failed with status {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return {
                'success': False,
                'error': 'Code analysis service error',
                'details': str(e)
            }
    
    def debug_issue(self, error_message: str, code_context: str = None, 
                   stack_trace: str = None, language: str = None) -> Dict[str, Any]:
        """
        Debug a specific issue with error message and context
        
        Args:
            error_message: Error message or description
            code_context: Relevant code context
            stack_trace: Stack trace if available
            language: Programming language
            
        Returns:
            Debugging results dictionary
        """
        try:
            debug_request = {
                'error_message': error_message,
                'analysis_type': 'debug_issue',
                'options': {
                    'provide_solution': True,
                    'explain_cause': True,
                    'suggest_prevention': True
                }
            }
            
            if code_context:
                debug_request['code_context'] = code_context
            
            if stack_trace:
                debug_request['stack_trace'] = stack_trace
            
            if language:
                debug_request['language'] = language
            
            response = self.session.post(
                f"{self.api_url}/api/v1/debug",
                json=debug_request,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'debug_id': result.get('debug_id'),
                    'cause_analysis': result.get('cause_analysis', ''),
                    'solution': result.get('solution', ''),
                    'fixed_code': result.get('fixed_code', ''),
                    'prevention_tips': result.get('prevention_tips', []),
                    'related_docs': result.get('related_docs', []),
                    'confidence_score': result.get('confidence_score', 0),
                    'analyzed_at': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'Debug request failed with status {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            logger.error(f"Debug request failed: {e}")
            return {
                'success': False,
                'error': 'Debug service error',
                'details': str(e)
            }
    
    def get_file_suggestions(self, file_path: str, file_content: str, 
                           language: str = None) -> Dict[str, Any]:
        """
        Get suggestions for a specific file
        
        Args:
            file_path: Path to the file
            file_content: Content of the file
            language: Programming language (auto-detected if not provided)
            
        Returns:
            File suggestions dictionary
        """
        try:
            # Auto-detect language if not provided
            if not language:
                language = self._detect_language_from_path(file_path)
            
            suggestion_request = {
                'file_path': file_path,
                'file_content': file_content,
                'language': language,
                'analysis_type': 'file_suggestions',
                'options': {
                    'code_quality': True,
                    'performance': True,
                    'security': True,
                    'maintainability': True,
                    'documentation': True
                }
            }
            
            response = self.session.post(
                f"{self.api_url}/api/v1/analyze/file",
                json=suggestion_request,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'file_path': file_path,
                    'language': language,
                    'suggestions': result.get('suggestions', []),
                    'quality_score': result.get('quality_score', 0),
                    'issues_found': result.get('issues_found', []),
                    'improvements': result.get('improvements', []),
                    'analyzed_at': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'File analysis failed with status {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            logger.error(f"File analysis failed: {e}")
            return {
                'success': False,
                'error': 'File analysis service error',
                'details': str(e)
            }
    
    def get_analysis_status(self, analysis_id: str) -> Dict[str, Any]:
        """
        Get the status of an ongoing analysis
        
        Args:
            analysis_id: ID of the analysis to check
            
        Returns:
            Analysis status dictionary
        """
        try:
            response = self.session.get(
                f"{self.api_url}/api/v1/analysis/{analysis_id}/status",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'analysis_id': analysis_id,
                    'status': result.get('status', 'unknown'),
                    'progress': result.get('progress', 0),
                    'estimated_completion': result.get('estimated_completion'),
                    'current_step': result.get('current_step', ''),
                    'results_available': result.get('results_available', False)
                }
            else:
                return {
                    'success': False,
                    'error': f'Status check failed with status {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Analysis status check failed: {e}")
            return {
                'success': False,
                'error': 'Status check service error',
                'details': str(e)
            }
    
    def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        """
        Get the results of a completed analysis
        
        Args:
            analysis_id: ID of the analysis
            
        Returns:
            Analysis results dictionary
        """
        try:
            response = self.session.get(
                f"{self.api_url}/api/v1/analysis/{analysis_id}/results",
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'results': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'Results retrieval failed with status {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Analysis results retrieval failed: {e}")
            return {
                'success': False,
                'error': 'Results retrieval service error',
                'details': str(e)
            }
    
    def _parse_github_url(self, url: str) -> Dict[str, Any]:
        """Parse GitHub URL and extract repository information"""
        if not url:
            return {
                'valid': False,
                'errors': ['GitHub URL is required']
            }
        
        # GitHub URL patterns
        github_patterns = [
            r'^https://github\.com/([a-zA-Z0-9\-_\.]+)/([a-zA-Z0-9\-_\.]+)/?$',
            r'^git@github\.com:([a-zA-Z0-9\-_\.]+)/([a-zA-Z0-9\-_\.]+)\.git$'
        ]
        
        for pattern in github_patterns:
            match = re.match(pattern, url)
            if match:
                owner, repo = match.groups()
                return {
                    'valid': True,
                    'owner': owner,
                    'repo': repo,
                    'normalized_url': f'https://github.com/{owner}/{repo}',
                    'errors': []
                }
        
        return {
            'valid': False,
            'errors': ['Invalid GitHub repository URL format']
        }
    
    def _detect_language_from_path(self, file_path: str) -> str:
        """Detect programming language from file path"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.sh': 'bash',
            '.bash': 'bash',
            '.ps1': 'powershell',
            '.dockerfile': 'dockerfile',
            '.md': 'markdown'
        }
        
        # Get file extension
        import os
        _, ext = os.path.splitext(file_path.lower())
        
        # Handle special cases
        filename = os.path.basename(file_path.lower())
        if filename == 'dockerfile':
            return 'dockerfile'
        if filename == 'makefile':
            return 'makefile'
        
        return extension_map.get(ext, 'text')
    
    def create_analysis_session(self, user_id: int) -> Dict[str, Any]:
        """
        Create a new analysis session for a user
        
        Args:
            user_id: ID of the user creating the session
            
        Returns:
            Session information dictionary
        """
        try:
            session_request = {
                'user_id': user_id,
                'session_type': 'code_analysis',
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = self.session.post(
                f"{self.api_url}/api/v1/sessions",
                json=session_request,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'session_id': result.get('session_id'),
                    'expires_at': result.get('expires_at'),
                    'created_at': result.get('created_at')
                }
            else:
                return {
                    'success': False,
                    'error': f'Session creation failed with status {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Analysis session creation failed: {e}")
            return {
                'success': False,
                'error': 'Session creation service error',
                'details': str(e)
            }
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages"""
        try:
            response = self.session.get(
                f"{self.api_url}/api/v1/languages",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('languages', [])
            else:
                # Return default supported languages
                return [
                    'python', 'javascript', 'typescript', 'java', 'cpp', 'c',
                    'csharp', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin',
                    'scala', 'r', 'sql', 'html', 'css', 'json', 'yaml'
                ]
                
        except Exception:
            # Return default supported languages
            return [
                'python', 'javascript', 'typescript', 'java', 'cpp', 'c',
                'csharp', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin',
                'scala', 'r', 'sql', 'html', 'css', 'json', 'yaml'
            ]

# Global Kimi-Dev service instance
kimi_service = KimiDevService()
