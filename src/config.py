"""
Configuration settings for the Cloud Browser Service
"""
import os
from datetime import timedelta
from pathlib import Path

class Config:
    """Base configuration class"""
    
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Database configuration
    BASE_DIR = Path(__file__).parent.parent.absolute()
    DATABASE_DIR = BASE_DIR / 'database'
    DATABASE_DIR.mkdir(exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DATABASE_DIR}/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT configuration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # Security configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Flask-Security configuration
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'password-salt-change-in-production')
    SECURITY_REGISTERABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_TWO_FACTOR = True
    SECURITY_TWO_FACTOR_ENABLED_METHODS = ['authenticator']
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = "100 per hour"
    
    # CORS configuration
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5173', 'https://localhost:3000']
    
    # Docker configuration
    DOCKER_HOST = os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock')
    DOCKER_NETWORK = os.environ.get('DOCKER_NETWORK', 'cloud-browser-network')
    
    # Browser container settings
    CONTAINER_CPU_LIMIT = float(os.environ.get('CONTAINER_CPU_LIMIT', '1.0'))
    CONTAINER_MEMORY_LIMIT = os.environ.get('CONTAINER_MEMORY_LIMIT', '2g')
    CONTAINER_TIMEOUT = int(os.environ.get('CONTAINER_TIMEOUT', '3600'))  # 1 hour
    MAX_CONTAINERS_PER_USER = int(os.environ.get('MAX_CONTAINERS_PER_USER', '3'))
    
    # Browser images
    FIREFOX_IMAGE = os.environ.get('FIREFOX_IMAGE', 'kasmweb/firefox:1.14.0')
    CHROME_IMAGE = os.environ.get('CHROME_IMAGE', 'kasmweb/chrome:1.14.0')
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = BASE_DIR / 'logs'
    LOG_DIR.mkdir(exist_ok=True)
    
    # Mail configuration (for password reset, etc.)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@cloudbrowser.local')
    
    # Admin user configuration
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@secure-kimi.local')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'SecureKimi2024!')
    
    # Kimi-Dev-72B Integration
    KIMI_DEV_API_URL = os.environ.get('KIMI_DEV_API_URL', 'http://localhost:8000')
    KIMI_DEV_API_KEY = os.environ.get('KIMI_DEV_API_KEY', '')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    WTF_CSRF_ENABLED = True
    
    # Production logging
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
