"""
API blueprint initialization for the Cloud Browser Service
"""
from flask import Blueprint
from .auth import auth_bp
from .sessions import sessions_bp
from .admin import admin_bp
from .kimi import kimi_bp
from .health import health_bp

# Create main API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Register sub-blueprints
api_bp.register_blueprint(auth_bp, url_prefix='/auth')
api_bp.register_blueprint(sessions_bp, url_prefix='/sessions')
api_bp.register_blueprint(admin_bp, url_prefix='/admin')
api_bp.register_blueprint(kimi_bp, url_prefix='/kimi')
api_bp.register_blueprint(health_bp, url_prefix='/health')

__all__ = ['api_bp']
