"""
Main Flask application entry point for Cloud Browser Service
"""
import os
import sys
import logging
from pathlib import Path
from flask import Flask, request, g, jsonify
from flask_cors import CORS
from datetime import datetime
import click

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from models.user import db
from auth.jwt_manager import jwt_manager
from api import api_bp
from utils.logging_config import setup_logging, log_request
from utils.database_helpers import init_database, check_database_health
from utils.response_helpers import error_response

def create_app(config_name=None):
    """
    Create and configure Flask application
    
    Args:
        config_name: Configuration name (development, production, testing)
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Set up logging
    setup_logging(app)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Cloud Browser Service in {config_name} mode")
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register middleware
    register_middleware(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    # Initialize database if needed
    with app.app_context():
        try:
            init_database(app)
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            if config_name != 'testing':
                raise
    
    logger.info("Cloud Browser Service initialized successfully")
    return app

def initialize_extensions(app):
    """Initialize Flask extensions"""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize database
        db.init_app(app)
        logger.info("Database initialized")
        
        # Initialize JWT manager
        jwt_manager.init_app(app)
        logger.info("JWT manager initialized")
        
        # Initialize CORS
        CORS(app, 
             origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
             allow_headers=['Content-Type', 'Authorization'],
             methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
        logger.info("CORS initialized")
        
    except Exception as e:
        logger.error(f"Extension initialization failed: {e}")
        raise

def register_blueprints(app):
    """Register Flask blueprints"""
    logger = logging.getLogger(__name__)
    
    try:
        # Register main API blueprint
        app.register_blueprint(api_bp)
        logger.info("API blueprints registered")
        
        # Register static file serving for frontend
        @app.route('/')
        @app.route('/<path:path>')
        def serve_frontend(path=''):
            """Serve frontend static files"""
            from flask import send_from_directory, send_file
            
            static_dir = Path(app.root_path) / 'static'
            
            if path and (static_dir / path).exists():
                return send_from_directory(static_dir, path)
            else:
                # Serve index.html for SPA routing
                index_file = static_dir / 'index.html'
                if index_file.exists():
                    return send_file(index_file)
                else:
                    return jsonify({
                        'message': 'Cloud Browser Service API',
                        'version': '1.0.0',
                        'status': 'running',
                        'timestamp': datetime.utcnow().isoformat()
                    })
        
    except Exception as e:
        logger.error(f"Blueprint registration failed: {e}")
        raise

def register_middleware(app):
    """Register middleware functions"""
    logger = logging.getLogger(__name__)
    
    @app.before_request
    def before_request():
        """Execute before each request"""
        g.request_start_time = datetime.utcnow()
        
        # Log request
        if app.config.get('LOG_REQUESTS', True):
            logger.debug(f"Request: {request.method} {request.url}")
    
    @app.after_request
    def after_request(response):
        """Execute after each request"""
        try:
            # Calculate request duration
            if hasattr(g, 'request_start_time'):
                duration = (datetime.utcnow() - g.request_start_time).total_seconds() * 1000
                
                # Log request completion
                if app.config.get('LOG_REQUESTS', True):
                    log_request(request, response, duration)
            
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            if app.config.get('ENV') == 'production':
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            # Add CORS headers if not already set
            if 'Access-Control-Allow-Origin' not in response.headers:
                origin = request.headers.get('Origin')
                allowed_origins = app.config.get('CORS_ORIGINS', [])
                if origin in allowed_origins:
                    response.headers['Access-Control-Allow-Origin'] = origin
            
        except Exception as e:
            logger.error(f"After request middleware error: {e}")
        
        return response
    
    @app.teardown_appcontext
    def teardown_db(error):
        """Clean up after request"""
        try:
            if error:
                db.session.rollback()
            else:
                db.session.commit()
        except Exception as e:
            logger.error(f"Database commit error: {e}")
            db.session.rollback()
        finally:
            db.session.remove()

def register_error_handlers(app):
    """Register error handlers"""
    logger = logging.getLogger(__name__)
    
    @app.errorhandler(400)
    def bad_request(error):
        return error_response(
            'bad_request',
            'The request could not be understood by the server'
        ), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return error_response(
            'unauthorized',
            'Authentication credentials were not provided or are invalid'
        ), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return error_response(
            'forbidden',
            'You do not have permission to access this resource'
        ), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return error_response(
            'not_found',
            'The requested resource was not found'
        ), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return error_response(
            'method_not_allowed',
            'The method is not allowed for the requested URL'
        ), 405
    
    @app.errorhandler(413)
    def payload_too_large(error):
        return error_response(
            'payload_too_large',
            'The request payload is too large'
        ), 413
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return error_response(
            'rate_limit_exceeded',
            'Too many requests. Please try again later.'
        ), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"Internal server error: {error}")
        return error_response(
            'internal_server_error',
            'An internal server error occurred'
        ), 500
    
    @app.errorhandler(502)
    def bad_gateway(error):
        return error_response(
            'bad_gateway',
            'Bad gateway error'
        ), 502
    
    @app.errorhandler(503)
    def service_unavailable(error):
        return error_response(
            'service_unavailable',
            'The service is temporarily unavailable'
        ), 503

def register_cli_commands(app):
    """Register CLI commands"""
    
    @app.cli.command()
    def init_db():
        """Initialize the database."""
        init_database(app)
        click.echo('Database initialized.')
    
    @app.cli.command()
    def check_health():
        """Check application health."""
        health = check_database_health()
        if health['healthy']:
            click.echo('✅ Application is healthy')
        else:
            click.echo('❌ Application has issues:')
            for issue in health['issues']:
                click.echo(f'  - {issue}')
    
    @app.cli.command()
    def create_admin():
        """Create admin user."""
        from utils.database_helpers import create_admin_user
        create_admin_user()
        click.echo('Admin user created.')
    
    @app.cli.command()
    @click.option('--cleanup-sessions', is_flag=True, help='Clean up old sessions')
    @click.option('--cleanup-logs', is_flag=True, help='Clean up old audit logs')
    def cleanup(cleanup_sessions, cleanup_logs):
        """Clean up old database records."""
        from utils.database_helpers import cleanup_database
        
        if cleanup_sessions or cleanup_logs:
            result = cleanup_database()
            click.echo(f'Cleanup completed: {result}')
        else:
            click.echo('No cleanup options specified. Use --help for options.')
    
    @app.cli.command()
    @click.argument('backup_path')
    def backup_db(backup_path):
        """Backup database to specified path."""
        from utils.database_helpers import backup_database
        backup_database(backup_path)
        click.echo(f'Database backed up to: {backup_path}')
    
    @app.cli.command()
    @click.argument('backup_path')
    def restore_db(backup_path):
        """Restore database from backup."""
        from utils.database_helpers import restore_database
        restore_database(backup_path)
        click.echo(f'Database restored from: {backup_path}')

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cloud Browser Service')
    parser.add_argument('--config', default='development',
                       choices=['development', 'production', 'testing'],
                       help='Configuration mode')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to bind to')
    parser.add_argument('--init-db', action='store_true',
                       help='Initialize database and exit')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create application
    app = create_app(args.config)
    
    if args.init_db:
        with app.app_context():
            init_database(app)
        print("Database initialized successfully")
        return
    
    # Run application
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug or args.config == 'development'
        )
    except KeyboardInterrupt:
        print("\nShutting down Cloud Browser Service...")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
